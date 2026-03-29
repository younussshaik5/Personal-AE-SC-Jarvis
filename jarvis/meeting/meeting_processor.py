#!/usr/bin/env python3
"""
Meeting processing pipeline orchestrator.
Coordinates transcription, video analysis, and output generation.

Key improvements over v1:
- Two-phase pipeline: fast path (quick transcript + key frames) then deep path (full analysis)
- Concurrency guard: only 1 recording processed at a time (configurable)
- Non-blocking loop: uses asyncio.create_task so the watcher doesn't stall
- Auto-cleanup: deletes processed files older than retention_days
- Dynamic timeouts: scale with file size for ffmpeg operations
"""

import asyncio
import json
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.meeting.transcriber import MeetingTranscriber
from jarvis.meeting.video_analyzer import VideoAnalyzer
from jarvis.meeting.recording_router import RecordingRouter


class MeetingProcessor:
    """
    Orchestrates the full meeting processing pipeline with two phases:

    Phase 1 (Fast Path, ~2 min):
      - Extract audio from video
      - Transcribe audio (parallel chunks if large)
      - Analyze 5-10 representative video frames (fast path)
      - Write quick transcript + publish "meeting.quick.ready"

    Phase 2 (Deep Path, background):
      - Extract all frames at 30s interval
      - Batch-analyze all frames in parallel
      - Write full visual analysis JSON
      - Publish "meeting.analysis.ready"

    Drop any recording in MEETINGS/ — JARVIS identifies the account automatically.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("meeting.processor")
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None
        self._active_tasks: Set[asyncio.Task] = set()

        # Read config
        meeting_cfg = getattr(self.config.config, "meeting", {})
        if isinstance(meeting_cfg, dict):
            self._max_concurrent = meeting_cfg.get("max_concurrent_recordings", 1)
            self._chunk_duration = meeting_cfg.get("chunk_duration_seconds", 600)
            self._chunk_overlap = meeting_cfg.get("chunk_overlap_seconds", 30)
            self._max_parallel_api = meeting_cfg.get("max_parallel_api_calls", 5)
            self._ffmpeg_timeout_per_gb = meeting_cfg.get("ffmpeg_timeout_per_gb", 600)
            self._retention_days = meeting_cfg.get("processed_retention_days", 7)
            self._fast_frame_interval = meeting_cfg.get("fast_path_frame_interval", 120)
            self._deep_frame_interval = meeting_cfg.get("deep_path_frame_interval", 30)
            self._transcription_model = meeting_cfg.get(
                "transcription_model", "nvidia/parakeet-ctc-1.1b-asr"
            )
        else:
            self._max_concurrent = 1
            self._chunk_duration = 600
            self._chunk_overlap = 30
            self._max_parallel_api = 5
            self._ffmpeg_timeout_per_gb = 600
            self._retention_days = 7
            self._fast_frame_interval = 120
            self._deep_frame_interval = 30
            self._transcription_model = "nvidia/parakeet-ctc-1.1b-asr"

        # Concurrency guard — only N recordings at a time
        self._processing_lock = asyncio.Semaphore(self._max_concurrent)

        # Initialize sub-components with NVIDIA config
        llm_cfg = getattr(self.config.config, "llm", {})
        nvidia_key = llm_cfg.get("api_key", "")
        nvidia_url = llm_cfg.get("base_url", "https://integrate.api.nvidia.com/v1")

        self.transcriber = MeetingTranscriber(
            nvidia_key, nvidia_url,
            model=self._transcription_model,
            chunk_duration=self._chunk_duration,
            chunk_overlap=self._chunk_overlap,
            max_parallel=self._max_parallel_api,
            ffmpeg_timeout_per_gb=self._ffmpeg_timeout_per_gb,
        )
        self.video_analyzer = VideoAnalyzer(
            nvidia_key, nvidia_url,
            max_parallel=self._max_parallel_api,
            ffmpeg_timeout_per_gb=self._ffmpeg_timeout_per_gb,
        )

        # Router identifies which account a recording belongs to
        accounts_dir = Path(self.config.workspace_root) / "ACCOUNTS"
        self.router = RecordingRouter(accounts_dir, nvidia_key, nvidia_url)

    async def start(self):
        """Start the meeting processor and auto-watch the MEETINGS/ folder."""
        self._running = True
        meetings_dir = Path(self.config.workspace_root) / "MEETINGS"
        meetings_dir.mkdir(parents=True, exist_ok=True)
        self._watch_task = asyncio.create_task(
            self.watch_queue(str(meetings_dir))
        )
        self.logger.info(
            "Meeting processor started",
            watching=str(meetings_dir),
            max_concurrent=self._max_concurrent,
        )

    async def stop(self):
        """Stop the meeting processor and wait for active tasks."""
        self._running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

        # Wait for any in-flight processing to finish
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        self.logger.info("Meeting processor stopped")

    # ------------------------------------------------------------------
    # Two-phase processing pipeline
    # ------------------------------------------------------------------

    async def process_recording(
        self,
        recording_path: str,
        account_name: str,
        meeting_title: str,
    ) -> dict:
        """
        Run the full meeting processing pipeline on a recording.

        Phase 1 (Fast Path):
          1. Extract audio from video (if video)
          2. Transcribe audio (parallel chunks if large)
          3. Fast video analysis: representative frames only
          4. Write quick transcript + publish "meeting.quick.ready"

        Phase 2 (Deep Path):
          5. Full video frame analysis: all frames at 30s interval
          6. Write full visual analysis JSON + publish "meeting.analysis.ready"

        Args:
            recording_path: Path to the recording file.
            account_name: Account name for output directory.
            meeting_title: Title/label for the meeting.

        Returns:
            Dict with transcript, visual_analysis, and output paths.
        """
        async with self._processing_lock:
            return await self._process_recording_inner(
                recording_path, account_name, meeting_title
            )

    async def _process_recording_inner(
        self,
        recording_path: str,
        account_name: str,
        meeting_title: str,
    ) -> dict:
        """Inner processing logic (called within the concurrency lock)."""
        recording = Path(recording_path)
        if not recording.exists():
            raise FileNotFoundError(f"Recording not found: {recording_path}")

        start_time = time.time()
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = meeting_title.replace(" ", "_").replace("/", "-")[:50]

        workspace_root = Path(self.config.workspace_root)
        meetings_dir = workspace_root / "ACCOUNTS" / account_name / "meetings"
        meetings_dir.mkdir(parents=True, exist_ok=True)

        is_video = recording.suffix.lower() in (
            ".mp4", ".mov", ".avi", ".mkv", ".webm",
        )

        result = {
            "recording_path": recording_path,
            "account_name": account_name,
            "meeting_title": meeting_title,
            "date": date_str,
            "transcript": "",
            "visual_analysis": [],
            "visual_analysis_deep": [],
            "output_paths": {},
        }

        # ============================================================
        # PHASE 1: FAST PATH — get usable results quickly
        # ============================================================
        self.logger.info("=== PHASE 1: Fast path ===", recording=recording_path)

        # Step 1: Extract audio + transcribe + fast video analysis in parallel
        audio_path = recording_path
        audio_task = None
        video_fast_task = None

        if is_video:
            # Start audio extraction
            async def _extract_audio():
                return await self.transcriber.extract_audio_from_video(recording_path)

            audio_task = asyncio.create_task(_extract_audio())

            # Start fast video analysis in parallel with audio extraction
            async def _fast_video():
                return await self.video_analyzer.analyze_fast(
                    recording_path, max_frames=10
                )

            video_fast_task = asyncio.create_task(_fast_video())

            # Wait for audio extraction first
            try:
                audio_path = await audio_task
                result["output_paths"]["extracted_audio"] = audio_path
            except Exception as e:
                self.logger.error("Audio extraction failed", error=str(e))
                raise

        # Step 2: Transcribe audio
        self.logger.info("Transcribing audio (fast path)", audio=audio_path)
        try:
            transcript = await self.transcriber.transcribe_audio(audio_path)
            result["transcript"] = transcript
        except Exception as e:
            self.logger.error("Transcription failed", error=str(e))
            transcript = ""
            result["transcript"] = ""

        # Step 3: Get fast video analysis results (if video)
        fast_visual = []
        if is_video and video_fast_task:
            try:
                fast_visual = await video_fast_task
                result["visual_analysis"] = fast_visual
            except Exception as e:
                self.logger.warning("Fast video analysis failed", error=str(e))

        # Step 4: Write quick transcript
        transcript_filename = f"{date_str}_{safe_title}_transcript.md"
        transcript_path = meetings_dir / transcript_filename
        transcript_md = self._format_transcript_md(
            account_name, meeting_title, date_str, transcript, fast_visual
        )
        transcript_path.write_text(transcript_md, encoding="utf-8")
        result["output_paths"]["transcript"] = str(transcript_path)

        fast_elapsed = round(time.time() - start_time, 2)
        self.logger.info(
            "=== PHASE 1 COMPLETE (fast path) ===",
            account=account_name,
            elapsed_seconds=fast_elapsed,
        )

        # Publish fast-path event
        self.event_bus.publish(
            Event(
                type="meeting.quick.ready",
                source="meeting.processor",
                data={
                    "account_name": account_name,
                    "meeting_title": meeting_title,
                    "date": date_str,
                    "transcript_path": str(transcript_path),
                    "transcript_length": len(transcript),
                    "frames_analyzed": len(fast_visual),
                    "processing_seconds": fast_elapsed,
                },
            )
        )

        # Also publish meeting.ended for backward compatibility
        self.event_bus.publish(
            Event(
                type="meeting.ended",
                source="meeting.processor",
                data={
                    "account_name": account_name,
                    "meeting_title": meeting_title,
                    "date": date_str,
                    "transcript_path": str(transcript_path),
                    "slides_path": result["output_paths"].get("slides"),
                    "transcript_length": len(transcript),
                    "frames_analyzed": len(fast_visual),
                    "processing_seconds": fast_elapsed,
                },
            )
        )

        # ============================================================
        # PHASE 2: DEEP PATH — full analysis in background
        # ============================================================
        if is_video:
            self.logger.info("=== PHASE 2: Deep path ===", recording=recording_path)
            try:
                deep_visual = await self.video_analyzer.analyze_meeting_video(
                    recording_path, interval_seconds=self._deep_frame_interval
                )
                result["visual_analysis_deep"] = deep_visual

                # Use deep analysis as the primary visual analysis
                result["visual_analysis"] = deep_visual

                # Write full visual analysis JSON
                slides_filename = f"{date_str}_{safe_title}_slides.json"
                slides_path = meetings_dir / slides_filename
                slides_path.write_text(
                    json.dumps(deep_visual, indent=2, default=str),
                    encoding="utf-8",
                )
                result["output_paths"]["slides"] = str(slides_path)

                # Update transcript with deep analysis
                transcript_md = self._format_transcript_md(
                    account_name, meeting_title, date_str, transcript, deep_visual
                )
                transcript_path.write_text(transcript_md, encoding="utf-8")

                deep_elapsed = round(time.time() - start_time, 2)
                self.logger.info(
                    "=== PHASE 2 COMPLETE (deep path) ===",
                    account=account_name,
                    frames_analyzed=len(deep_visual),
                    total_elapsed_seconds=deep_elapsed,
                )

                # Publish deep analysis event
                self.event_bus.publish(
                    Event(
                        type="meeting.analysis.ready",
                        source="meeting.processor",
                        data={
                            "account_name": account_name,
                            "meeting_title": meeting_title,
                            "date": date_str,
                            "transcript_path": str(transcript_path),
                            "slides_path": str(slides_path),
                            "frames_analyzed": len(deep_visual),
                            "total_processing_seconds": deep_elapsed,
                        },
                    )
                )

            except Exception as e:
                self.logger.error("Deep video analysis failed", error=str(e))

        total_elapsed = round(time.time() - start_time, 2)
        self.logger.info(
            "Meeting processing complete",
            account=account_name,
            title=meeting_title,
            total_elapsed_seconds=total_elapsed,
        )

        return result

    # ------------------------------------------------------------------
    # File watcher — non-blocking, auto-cleanup
    # ------------------------------------------------------------------

    async def watch_queue(self, meetings_dir: str):
        """
        Watch the MEETINGS/ folder for new recording files.
        Processing is non-blocking — each file is dispatched as a task.
        """
        VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a"}

        meetings = Path(meetings_dir)
        meetings.mkdir(parents=True, exist_ok=True)
        processed_dir = meetings / ".processed"
        processed_dir.mkdir(exist_ok=True)

        self.logger.info("Watching MEETINGS folder", path=str(meetings))

        while self._running:
            try:
                # Clean up old processed files periodically
                self._cleanup_old_processed(processed_dir)

                for recording in sorted(meetings.iterdir()):
                    if not recording.is_file():
                        continue
                    if recording.suffix.lower() not in VIDEO_EXTS:
                        continue
                    if recording.name.startswith('.'):
                        continue

                    self.logger.info("New recording detected", file=recording.name)

                    # Dispatch processing as a non-blocking task
                    task = asyncio.create_task(
                        self._process_one_file(recording, processed_dir),
                        name=f"meeting-{recording.name}",
                    )
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)

            except Exception as e:
                self.logger.error("MEETINGS watcher error", error=str(e))

            await asyncio.sleep(10)

    async def _process_one_file(self, recording: Path, processed_dir: Path):
        """Process a single recording file — called from the watcher."""
        try:
            # Auto-identify account
            route = await self.router.identify_account(
                recording_path=recording,
                transcriber=self.transcriber,
                llm_client=None,
            )
            account_name = route["account"]
            confidence = route["confidence"]
            created_new = route["created_new"]

            self.logger.info(
                "Account identified",
                account=account_name,
                method=route["method"],
                confidence=confidence,
            )

            # Notify if low confidence or new account
            if route["notify"]:
                self.event_bus.publish(Event(
                    type="meeting.account.uncertain",
                    source="meeting.processor",
                    data={
                        "file": recording.name,
                        "account": account_name,
                        "confidence": confidence,
                        "created_new": created_new,
                        "message": (
                            f"Recording '{recording.name}' routed to "
                            f"{'NEW account' if created_new else 'account'} "
                            f"'{account_name}' (confidence: {confidence:.0%}). "
                            f"Please confirm or reassign."
                        )
                    }
                ))

            # Process the recording (acquires concurrency lock internally)
            meeting_title = recording.stem
            await self.process_recording(
                recording_path=str(recording),
                account_name=account_name,
                meeting_title=meeting_title,
            )

            # Move to .processed/
            recording.rename(processed_dir / recording.name)
            self.logger.info(
                "Recording processed and archived",
                file=recording.name,
                account=account_name,
            )

        except Exception as e:
            self.logger.error(
                "Failed to process recording",
                file=recording.name,
                error=str(e),
            )
            # Move to .processed/failed/ so it doesn't re-trigger
            failed_dir = processed_dir / "failed"
            failed_dir.mkdir(exist_ok=True)
            try:
                recording.rename(failed_dir / recording.name)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_old_processed(self, processed_dir: Path):
        """Delete processed files older than retention_days."""
        if not processed_dir.exists():
            return

        cutoff = time.time() - (self._retention_days * 86400)
        cleaned = 0

        try:
            for item in processed_dir.iterdir():
                if item.name in ("failed",):
                    # Don't clean the failed directory itself
                    # but clean old files inside it
                    if item.is_dir():
                        for failed_file in item.iterdir():
                            try:
                                if failed_file.stat().st_mtime < cutoff:
                                    failed_file.unlink()
                                    cleaned += 1
                            except OSError:
                                pass
                    continue

                try:
                    if item.is_file() and item.stat().st_mtime < cutoff:
                        item.unlink()
                        cleaned += 1
                    elif item.is_dir() and item.stat().st_mtime < cutoff:
                        shutil.rmtree(item, ignore_errors=True)
                        cleaned += 1
                except OSError:
                    pass
        except OSError:
            pass

        if cleaned > 0:
            self.logger.info(
                "Cleaned up old processed files",
                deleted=cleaned,
                retention_days=self._retention_days,
            )

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def _format_transcript_md(
        self,
        account_name: str,
        meeting_title: str,
        date_str: str,
        transcript: str,
        visual_analysis: list,
    ) -> str:
        """Format transcript and visual analysis as a markdown document."""
        lines = [
            f"# Meeting Transcript: {meeting_title}",
            f"**Account:** {account_name}",
            f"**Date:** {date_str}",
            f"**Generated by:** JARVIS Meeting Processor",
            "",
            "---",
            "",
            "## Transcript",
            "",
            transcript,
            "",
        ]

        if visual_analysis:
            lines.extend([
                "---",
                "",
                "## Visual Analysis (Slide Captures)",
                "",
            ])

            all_action_items = []
            all_competitive = []

            for frame in visual_analysis:
                ts = frame.get("timestamp_seconds", 0)
                minutes = ts // 60
                seconds = ts % 60
                timestamp_label = f"{minutes:02d}:{seconds:02d}"

                slide_content = frame.get("slide_content", "")
                if slide_content:
                    lines.append(f"### [{timestamp_label}]")
                    lines.append(f"{slide_content}")
                    lines.append("")

                for item in frame.get("action_items", []):
                    if item and item not in all_action_items:
                        all_action_items.append(item)

                for mention in frame.get("competitive_mentions", []):
                    if mention and mention not in all_competitive:
                        all_competitive.append(mention)

            if all_action_items:
                lines.extend([
                    "---",
                    "",
                    "## Action Items (from slides)",
                    "",
                ])
                for item in all_action_items:
                    lines.append(f"- [ ] {item}")
                lines.append("")

            if all_competitive:
                lines.extend([
                    "---",
                    "",
                    "## Competitive Mentions",
                    "",
                ])
                for mention in all_competitive:
                    lines.append(f"- {mention}")
                lines.append("")

        return "\n".join(lines)
