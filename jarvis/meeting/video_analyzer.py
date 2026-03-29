#!/usr/bin/env python3
"""
Video frame analysis using NVIDIA Cosmos-Reason2-8B for meeting slide
and content extraction.

Key improvements over v1:
- Parallel frame analysis (asyncio.gather + semaphore)
- Fast path: analyze only representative frames for quick results
- Retry with exponential backoff on transient API errors
- Dynamic timeouts based on file size
"""

import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.retry import retry


class VideoAnalyzer:
    """Analyzes meeting video frames using NVIDIA Cosmos-Reason2-8B vision model."""

    def __init__(
        self,
        nvidia_api_key: str,
        nvidia_base_url: str,
        max_parallel: int = 5,
        ffmpeg_timeout_per_gb: int = 600,
    ):
        self.nvidia_api_key = nvidia_api_key
        self.nvidia_base_url = nvidia_base_url.rstrip("/")
        self.max_parallel = max_parallel
        self.ffmpeg_timeout_per_gb = ffmpeg_timeout_per_gb
        self.logger = JARVISLogger("meeting.video_analyzer")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_frames(
        self, video_path: str, interval_seconds: int = 30
    ) -> List[str]:
        """
        Extract frames from a video at regular intervals using ffmpeg.

        Args:
            video_path: Path to the video file.
            interval_seconds: Seconds between extracted frames.

        Returns:
            List of paths to extracted JPEG frame files.
        """
        video = Path(video_path)
        if not video.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        frames_dir = Path(tempfile.mkdtemp(prefix="jarvis_frames_"))
        frame_pattern = str(frames_dir / "frame_%05d.jpg")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"fps=1/{interval_seconds}",
            "-q:v", "3",
            "-frame_pts", "1",
            frame_pattern,
        ]

        timeout = self._get_ffmpeg_timeout(video_path)
        self.logger.info(
            "Extracting frames",
            video=video_path,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout,
        )

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(
                f"Frame extraction timed out after {timeout}s for {video_path}"
            )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Frame extraction failed: {stderr.decode()[:500]}"
            )

        frames = sorted(frames_dir.glob("frame_*.jpg"))
        self.logger.info(
            "Frames extracted",
            video=video_path,
            count=len(frames),
            interval_seconds=interval_seconds,
        )
        return [str(f) for f in frames]

    async def analyze_frame(self, frame_path: str) -> dict:
        """
        Analyze a single video frame using Cosmos-Reason2-8B via OpenAI vision API.

        Extracts:
        - slide_content: Text/content visible on any presentation slides
        - action_items: Any action items or tasks mentioned/shown
        - competitive_mentions: References to competitors or competing products
        - presenter_sentiment: Overall sentiment/energy of the presenter

        Args:
            frame_path: Path to a JPEG frame file.

        Returns:
            Dict with structured analysis.
        """
        frame = Path(frame_path)
        if not frame.exists():
            raise FileNotFoundError(f"Frame not found: {frame_path}")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for video analysis. "
                "Install with: pip install openai"
            )

        # Encode frame as base64
        with open(frame_path, "rb") as f:
            frame_b64 = base64.b64encode(f.read()).decode("utf-8")

        client = OpenAI(
            api_key=self.nvidia_api_key,
            base_url=self.nvidia_base_url,
        )

        analysis_prompt = """Analyze this meeting screenshot and extract the following in JSON format:

{
  "slide_content": "Text and key content visible on any presentation slides or shared screen. If no slides visible, describe what is shown.",
  "action_items": ["List of any action items, tasks, or next steps mentioned or shown"],
  "competitive_mentions": ["Any competitor names, products, or comparative references visible"],
  "presenter_sentiment": "Brief assessment of presenter energy/sentiment: positive, neutral, concerned, enthusiastic, etc."
}

Be precise and extract only what is clearly visible. If a field has no relevant content, use empty string or empty list."""

        return await self._analyze_frame_with_retry(
            client, frame_b64, analysis_prompt, frame_path
        )

    async def analyze_meeting_video(
        self, video_path: str, interval_seconds: int = 30
    ) -> List[dict]:
        """
        Extract frames from a meeting video and analyze all of them in parallel.

        Args:
            video_path: Path to the meeting video file.
            interval_seconds: Seconds between extracted frames.

        Returns:
            List of analysis dicts, one per extracted frame.
        """
        self.logger.info("Starting full video analysis", video=video_path)

        frames = await self.extract_frames(video_path, interval_seconds=interval_seconds)

        if not frames:
            self.logger.warning("No frames extracted", video=video_path)
            return []

        # Analyze all frames in parallel with bounded concurrency
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def _analyze_with_limit(i, frame_path):
            async with semaphore:
                self.logger.debug(
                    f"Analyzing frame {i + 1}/{len(frames)}",
                    frame=frame_path,
                )
                analysis = await self.analyze_frame(frame_path)
                analysis["frame_index"] = i
                analysis["timestamp_seconds"] = i * interval_seconds
                return analysis

        analyses = await asyncio.gather(
            *[_analyze_with_limit(i, fp) for i, fp in enumerate(frames)],
            return_exceptions=True,
        )

        # Separate successes from failures
        results = []
        for i, result in enumerate(analyses):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Frame {i} analysis failed",
                    error=str(result),
                )
                results.append({
                    "slide_content": "",
                    "action_items": [],
                    "competitive_mentions": [],
                    "presenter_sentiment": "unknown",
                    "frame_path": frames[i],
                    "frame_index": i,
                    "timestamp_seconds": i * interval_seconds,
                    "error": str(result),
                })
            else:
                results.append(result)

        # Cleanup extracted frames
        self._cleanup_frames(frames)

        self.logger.info(
            "Video analysis complete",
            video=video_path,
            frames_analyzed=len(results),
        )
        return results

    async def analyze_fast(
        self, video_path: str, max_frames: int = 10
    ) -> List[dict]:
        """
        Fast path: extract frames at a wide interval and analyze only a subset.

        For a 2-hour video with 120s interval, this produces ~60 frames,
        then analyzes only the first `max_frames` representative frames.
        Results come back in ~1-2 minutes instead of 8+.

        Args:
            video_path: Path to the meeting video file.
            max_frames: Maximum number of frames to analyze.

        Returns:
            List of analysis dicts for representative frames.
        """
        self.logger.info("Starting FAST video analysis", video=video_path)

        # Extract frames at 120s interval (5x fewer than deep path)
        frames = await self.extract_frames(video_path, interval_seconds=120)

        if not frames:
            self.logger.warning("No frames extracted", video=video_path)
            return []

        # Take first N frames (most likely to have intro slides)
        frames_to_analyze = frames[:max_frames]

        semaphore = asyncio.Semaphore(self.max_parallel)

        async def _analyze_with_limit(i, frame_path):
            async with semaphore:
                analysis = await self.analyze_frame(frame_path)
                analysis["frame_index"] = i
                analysis["timestamp_seconds"] = i * 120
                return analysis

        analyses = await asyncio.gather(
            *[_analyze_with_limit(i, fp) for i, fp in enumerate(frames_to_analyze)],
            return_exceptions=True,
        )

        results = []
        for i, result in enumerate(analyses):
            if isinstance(result, Exception):
                results.append({
                    "slide_content": "",
                    "action_items": [],
                    "competitive_mentions": [],
                    "presenter_sentiment": "unknown",
                    "frame_path": frames_to_analyze[i],
                    "frame_index": i,
                    "timestamp_seconds": i * 120,
                    "error": str(result),
                })
            else:
                results.append(result)

        # Cleanup all frames (including unanalyzed ones)
        self._cleanup_frames(frames)

        self.logger.info(
            "Fast video analysis complete",
            video=video_path,
            frames_analyzed=len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @retry(max_attempts=3, backoff_base=2.0)
    async def _analyze_frame_with_retry(
        self, client, frame_b64: str, prompt: str, frame_path: str
    ) -> dict:
        """Analyze a single frame with retry on transient errors."""
        try:
            response = client.chat.completions.create(
                model="nvidia/cosmos-reason2-8b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame_b64}",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1024,
                temperature=0.2,
            )

            raw_text = response.choices[0].message.content.strip()

            # Parse JSON from response (handle markdown code blocks)
            json_text = raw_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            try:
                analysis = json.loads(json_text.strip())
            except json.JSONDecodeError:
                analysis = {
                    "slide_content": raw_text,
                    "action_items": [],
                    "competitive_mentions": [],
                    "presenter_sentiment": "unknown",
                }

            # Ensure all expected keys exist
            analysis.setdefault("slide_content", "")
            analysis.setdefault("action_items", [])
            analysis.setdefault("competitive_mentions", [])
            analysis.setdefault("presenter_sentiment", "unknown")
            analysis["frame_path"] = frame_path

            return analysis

        except Exception as e:
            self.logger.error(
                "Frame analysis failed",
                frame=frame_path,
                error=str(e),
            )
            return {
                "slide_content": "",
                "action_items": [],
                "competitive_mentions": [],
                "presenter_sentiment": "unknown",
                "frame_path": frame_path,
                "error": str(e),
            }

    def _cleanup_frames(self, frame_paths: List[str]):
        """Clean up extracted frame files and temp directory."""
        parent_dir = None
        for frame_path in frame_paths:
            try:
                p = Path(frame_path)
                if parent_dir is None:
                    parent_dir = p.parent
                p.unlink(missing_ok=True)
            except OSError:
                pass

        if parent_dir:
            try:
                shutil.rmtree(parent_dir, ignore_errors=True)
            except Exception:
                pass

    def _get_ffmpeg_timeout(self, file_path: str) -> int:
        """Dynamic timeout based on file size: min 300s, +600s per GB."""
        try:
            size_gb = Path(file_path).stat().st_size / (1024 ** 3)
        except Exception:
            size_gb = 1.0
        return max(300, int(size_gb * self.ffmpeg_timeout_per_gb))
