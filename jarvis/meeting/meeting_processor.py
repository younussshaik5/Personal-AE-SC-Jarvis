#!/usr/bin/env python3
"""
Meeting processing pipeline orchestrator.
Coordinates transcription, video analysis, and output generation.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.meeting.transcriber import MeetingTranscriber
from jarvis.meeting.video_analyzer import VideoAnalyzer
from jarvis.meeting.recording_router import RecordingRouter


class MeetingProcessor:
    """
    Orchestrates the full meeting processing pipeline:
    audio extraction -> transcription -> video frame analysis -> output generation.

    Drop any recording in MEETINGS/ — JARVIS identifies the account automatically.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("meeting.processor")
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None

        # Initialize sub-components with NVIDIA config from LLM settings
        llm_cfg = getattr(self.config.config, "llm", {})
        nvidia_key = llm_cfg.get("api_key", "")
        nvidia_url = llm_cfg.get("base_url", "https://integrate.api.nvidia.com/v1")

        self.transcriber = MeetingTranscriber(nvidia_key, nvidia_url)
        self.video_analyzer = VideoAnalyzer(nvidia_key, nvidia_url)

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
        self.logger.info("Meeting processor started", watching=str(meetings_dir))

    async def stop(self):
        """Stop the meeting processor."""
        self._running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Meeting processor stopped")

    async def process_recording(
        self,
        recording_path: str,
        account_name: str,
        meeting_title: str,
    ) -> dict:
        """
        Run the full meeting processing pipeline on a recording.

        Pipeline:
        1. Extract audio from video (if video file)
        2. Transcribe audio via MeetingTranscriber
        3. Extract and analyze video frames via VideoAnalyzer (if video)
        4. Combine transcript + visual analysis
        5. Write transcript to ACCOUNTS/{account}/meetings/
        6. Write visual analysis JSON to ACCOUNTS/{account}/meetings/
        7. Publish meeting.ended event
        8. Return combined data

        Args:
            recording_path: Path to the recording file (video or audio).
            account_name: Account name for output directory.
            meeting_title: Title/label for the meeting.

        Returns:
            Dict with transcript, visual_analysis, and output paths.
        """
        recording = Path(recording_path)
        if not recording.exists():
            raise FileNotFoundError(f"Recording not found: {recording_path}")

        start_time = time.time()
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = meeting_title.replace(" ", "_").replace("/", "-")

        # Determine output directory
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
            "output_paths": {},
        }

        # Step 1 & 2: Extract audio and transcribe
        audio_path = recording_path
        if is_video:
            self.logger.info(
                "Extracting audio from video", recording=recording_path
            )
            audio_path = await self.transcriber.extract_audio_from_video(
                recording_path
            )
            result["output_paths"]["extracted_audio"] = audio_path

        self.logger.info("Transcribing audio", audio=audio_path)
        transcript = await self.transcriber.transcribe_audio(audio_path)
        result["transcript"] = transcript

        # Step 3: Video frame analysis (if video)
        if is_video:
            self.logger.info(
                "Analyzing video frames", recording=recording_path
            )
            visual_analysis = await self.video_analyzer.analyze_meeting_video(
                recording_path
            )
            result["visual_analysis"] = visual_analysis

        # Step 4: Combine data (already in result dict)

        # Step 5: Write transcript markdown
        transcript_filename = f"{date_str}_{safe_title}_transcript.md"
        transcript_path = meetings_dir / transcript_filename
        transcript_md = self._format_transcript_md(
            account_name, meeting_title, date_str, transcript, result.get("visual_analysis", [])
        )
        transcript_path.write_text(transcript_md, encoding="utf-8")
        result["output_paths"]["transcript"] = str(transcript_path)
        self.logger.info("Transcript written", path=str(transcript_path))

        # Step 6: Write visual analysis JSON (if video)
        if result["visual_analysis"]:
            slides_filename = f"{date_str}_{safe_title}_slides.json"
            slides_path = meetings_dir / slides_filename
            slides_path.write_text(
                json.dumps(result["visual_analysis"], indent=2, default=str),
                encoding="utf-8",
            )
            result["output_paths"]["slides"] = str(slides_path)
            self.logger.info("Visual analysis written", path=str(slides_path))

        # Step 7: Publish meeting.ended event
        elapsed = round(time.time() - start_time, 2)
        self.event_bus.publish(
            Event(
                type="meeting.ended",
                source="meeting.processor",
                data={
                    "account_name": account_name,
                    "meeting_title": meeting_title,
                    "date": date_str,
                    "transcript_path": result["output_paths"].get("transcript"),
                    "slides_path": result["output_paths"].get("slides"),
                    "transcript_length": len(transcript),
                    "frames_analyzed": len(result["visual_analysis"]),
                    "processing_seconds": elapsed,
                },
            )
        )

        self.logger.info(
            "Meeting processing complete",
            account=account_name,
            title=meeting_title,
            elapsed_seconds=elapsed,
        )

        # Step 8: Return combined data
        return result

    async def watch_queue(self, meetings_dir: str):
        """
        Watch the MEETINGS/ folder for new recording files.

        Drop ANY video/audio file here — JARVIS identifies the account automatically
        using RecordingRouter (filename → quick transcript → full NLP → new account).

        Supported formats: .mp4 .mov .avi .mkv .webm .mp3 .wav .m4a

        Processed files are moved to MEETINGS/.processed/ so they don't re-trigger.
        """
        VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a"}

        meetings = Path(meetings_dir)
        meetings.mkdir(parents=True, exist_ok=True)
        processed_dir = meetings / ".processed"
        processed_dir.mkdir(exist_ok=True)

        self.logger.info("Watching MEETINGS folder", path=str(meetings))

        while self._running:
            try:
                for recording in sorted(meetings.iterdir()):
                    if not recording.is_file():
                        continue
                    if recording.suffix.lower() not in VIDEO_EXTS:
                        continue
                    if recording.name.startswith('.'):
                        continue

                    self.logger.info("New recording detected", file=recording.name)

                    try:
                        # Auto-identify account
                        route = await self.router.identify_account(
                            recording_path=recording,
                            transcriber=self.transcriber,
                            llm_client=None,  # use LLM only as last resort
                        )
                        account_name = route["account"]
                        method = route["method"]
                        confidence = route["confidence"]
                        created_new = route["created_new"]

                        self.logger.info(
                            "Account identified",
                            account=account_name,
                            method=method,
                            confidence=confidence,
                        )

                        # Notify if low confidence or new account created
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

                        # Process the recording
                        meeting_title = recording.stem
                        await self.process_recording(
                            recording_path=str(recording),
                            account_name=account_name,
                            meeting_title=meeting_title,
                        )

                        # Move to .processed/
                        recording.rename(processed_dir / recording.name)
                        self.logger.info("Recording processed and archived",
                                         file=recording.name, account=account_name)

                    except Exception as e:
                        self.logger.error("Failed to process recording",
                                          file=recording.name, error=str(e))
                        # Move to .processed/failed/ so it doesn't loop
                        failed_dir = processed_dir / "failed"
                        failed_dir.mkdir(exist_ok=True)
                        recording.rename(failed_dir / recording.name)

            except Exception as e:
                self.logger.error("MEETINGS watcher error", error=str(e))

            await asyncio.sleep(10)  # check every 10 seconds

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

            # Aggregate unique action items and competitive mentions
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
