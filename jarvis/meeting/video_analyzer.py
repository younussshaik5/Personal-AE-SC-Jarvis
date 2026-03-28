#!/usr/bin/env python3
"""
Video frame analysis using NVIDIA Cosmos-Reason2-8B for meeting slide
and content extraction.
"""

import base64
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from jarvis.utils.logger import JARVISLogger


class VideoAnalyzer:
    """Analyzes meeting video frames using NVIDIA Cosmos-Reason2-8B vision model."""

    def __init__(self, nvidia_api_key: str, nvidia_base_url: str):
        """
        Args:
            nvidia_api_key: API key for NVIDIA NIM endpoints.
            nvidia_base_url: Base URL for the NVIDIA API.
        """
        self.nvidia_api_key = nvidia_api_key
        self.nvidia_base_url = nvidia_base_url.rstrip("/")
        self.logger = JARVISLogger("meeting.video_analyzer")

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
            "-q:v", "3",  # JPEG quality (2=best, 31=worst)
            "-frame_pts", "1",
            frame_pattern,
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(
                f"Frame extraction failed: {proc.stderr[:500]}"
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

        try:
            response = client.chat.completions.create(
                model="nvidia/cosmos-reason2-8b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt,
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
                # If JSON parsing fails, structure the raw text
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

    async def analyze_meeting_video(self, video_path: str) -> List[dict]:
        """
        Extract frames from a meeting video and analyze all of them.

        Args:
            video_path: Path to the meeting video file.

        Returns:
            List of analysis dicts, one per extracted frame.
        """
        self.logger.info("Starting full video analysis", video=video_path)

        frames = await self.extract_frames(video_path, interval_seconds=30)

        if not frames:
            self.logger.warning("No frames extracted", video=video_path)
            return []

        analyses = []
        for i, frame_path in enumerate(frames):
            self.logger.info(
                f"Analyzing frame {i + 1}/{len(frames)}",
                frame=frame_path,
            )
            analysis = await self.analyze_frame(frame_path)
            analysis["frame_index"] = i
            analysis["timestamp_seconds"] = i * 30
            analyses.append(analysis)

        # Cleanup extracted frames
        for frame_path in frames:
            try:
                Path(frame_path).unlink(missing_ok=True)
            except OSError:
                pass

        # Try to remove the temp directory
        if frames:
            try:
                Path(frames[0]).parent.rmdir()
            except OSError:
                pass

        self.logger.info(
            "Video analysis complete",
            video=video_path,
            frames_analyzed=len(analyses),
        )
        return analyses
