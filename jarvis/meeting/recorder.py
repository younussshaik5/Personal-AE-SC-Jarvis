#!/usr/bin/env python3
"""
Meeting recording utilities for macOS using screencapture and ffmpeg.
Captures screen video and system audio via BlackHole virtual audio device.
"""

import asyncio
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional

from jarvis.utils.logger import JARVISLogger


class MeetingRecorder:
    """Records meeting screen and audio on macOS."""

    def __init__(self):
        self.logger = JARVISLogger("meeting.recorder")
        self._screen_process: Optional[subprocess.Popen] = None
        self._audio_process: Optional[subprocess.Popen] = None
        self._recording_start_time: Optional[float] = None
        self._output_paths: dict = {}

    async def start_screen_recording(
        self, output_path: str, duration_minutes: int = 60
    ) -> bool:
        """
        Start screen recording using macOS screencapture or ffmpeg+avfoundation.

        Args:
            output_path: Path for the output video file (.mov or .mp4).
            duration_minutes: Maximum recording duration in minutes.

        Returns:
            True if recording started successfully.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        duration_seconds = duration_minutes * 60

        # Try screencapture first (native macOS, lower overhead)
        if output.suffix == ".mov":
            try:
                self._screen_process = subprocess.Popen(
                    ["screencapture", "-v", "-V", str(duration_seconds), str(output)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                self._recording_start_time = time.time()
                self._output_paths["screen"] = str(output)
                self.logger.info(
                    "Screen recording started (screencapture)",
                    path=str(output),
                    duration_minutes=duration_minutes,
                )
                return True
            except FileNotFoundError:
                self.logger.warning(
                    "screencapture not found, falling back to ffmpeg"
                )

        # Fallback: ffmpeg with avfoundation (works for .mp4 and when screencapture fails)
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "avfoundation",
                "-framerate", "15",
                "-capture_cursor", "1",
                "-i", "1:none",  # Screen index 1, no audio (audio captured separately)
                "-t", str(duration_seconds),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                str(output),
            ]
            self._screen_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
            self._recording_start_time = time.time()
            self._output_paths["screen"] = str(output)
            self.logger.info(
                "Screen recording started (ffmpeg/avfoundation)",
                path=str(output),
                duration_minutes=duration_minutes,
            )
            return True
        except FileNotFoundError:
            self.logger.error(
                "Neither screencapture nor ffmpeg available for screen recording"
            )
            return False

    async def start_audio_recording(
        self, output_path: str, duration_minutes: int = 60
    ) -> bool:
        """
        Start audio recording using ffmpeg with BlackHole virtual audio device.

        BlackHole must be installed and configured as a multi-output device
        to capture system/meeting audio.

        Args:
            output_path: Path for the output audio file (.wav or .m4a).
            duration_minutes: Maximum recording duration in minutes.

        Returns:
            True if recording started successfully.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        duration_seconds = duration_minutes * 60

        # Determine audio codec based on extension
        if output.suffix == ".wav":
            codec_args = ["-c:a", "pcm_s16le"]
        elif output.suffix in (".m4a", ".aac"):
            codec_args = ["-c:a", "aac", "-b:a", "128k"]
        else:
            codec_args = ["-c:a", "pcm_s16le"]

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "avfoundation",
                "-i", ":BlackHole 2ch",  # BlackHole virtual audio device
                "-t", str(duration_seconds),
                "-ac", "1",  # Mono for transcription
                "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
                *codec_args,
                str(output),
            ]
            self._audio_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
            self._output_paths["audio"] = str(output)
            self.logger.info(
                "Audio recording started (ffmpeg/BlackHole)",
                path=str(output),
                duration_minutes=duration_minutes,
            )
            return True
        except FileNotFoundError:
            self.logger.error("ffmpeg not found - cannot record audio")
            return False

    async def stop_recording(self) -> dict:
        """
        Stop all active recordings gracefully.

        Returns:
            Dict with paths to recorded files.
        """
        results = {}

        for label, process in [
            ("screen", self._screen_process),
            ("audio", self._audio_process),
        ]:
            if process and process.poll() is None:
                try:
                    # Send SIGINT for graceful ffmpeg shutdown (writes trailer)
                    process.send_signal(signal.SIGINT)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                    self.logger.info(f"{label} recording stopped")
                except Exception as e:
                    self.logger.error(
                        f"Error stopping {label} recording", error=str(e)
                    )
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass

            if label in self._output_paths:
                path = Path(self._output_paths[label])
                if path.exists() and path.stat().st_size > 0:
                    results[label] = str(path)

        self._screen_process = None
        self._audio_process = None
        self._recording_start_time = None

        self.logger.info("All recordings stopped", files=results)
        return results

    def get_recording_status(self) -> dict:
        """
        Check if recordings are currently active.

        Returns:
            Dict with recording status information.
        """
        screen_active = (
            self._screen_process is not None
            and self._screen_process.poll() is None
        )
        audio_active = (
            self._audio_process is not None
            and self._audio_process.poll() is None
        )

        elapsed = None
        if self._recording_start_time and (screen_active or audio_active):
            elapsed = round(time.time() - self._recording_start_time, 1)

        return {
            "screen_recording": screen_active,
            "audio_recording": audio_active,
            "any_active": screen_active or audio_active,
            "elapsed_seconds": elapsed,
            "output_paths": dict(self._output_paths),
        }
