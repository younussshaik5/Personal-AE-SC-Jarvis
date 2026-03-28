#!/usr/bin/env python3
"""
Meeting transcription using NVIDIA Whisper API (OpenAI-compatible endpoint)
with local whisper fallback.
"""

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from jarvis.utils.logger import JARVISLogger


class MeetingTranscriber:
    """Transcribes meeting audio using NVIDIA Whisper API or local whisper."""

    def __init__(self, nvidia_api_key: str, nvidia_base_url: str):
        """
        Args:
            nvidia_api_key: API key for NVIDIA NIM endpoints.
            nvidia_base_url: Base URL for the NVIDIA API (e.g. https://integrate.api.nvidia.com/v1).
        """
        self.nvidia_api_key = nvidia_api_key
        self.nvidia_base_url = nvidia_base_url.rstrip("/")
        self.logger = JARVISLogger("meeting.transcriber")

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe an audio file, trying NVIDIA API first then local whisper.

        Args:
            audio_path: Path to the audio file (.wav, .m4a, .mp3, etc.).

        Returns:
            Full transcript text.
        """
        audio = Path(audio_path)
        if not audio.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self.logger.info("Starting transcription", audio_path=audio_path)

        # Try NVIDIA API first
        if self.nvidia_api_key and self.nvidia_api_key != "YOUR_API_KEY_HERE":
            try:
                transcript = await self._transcribe_nvidia(audio_path)
                self.logger.info(
                    "Transcription complete (NVIDIA)",
                    length=len(transcript),
                )
                return transcript
            except Exception as e:
                self.logger.warning(
                    "NVIDIA transcription failed, falling back to local",
                    error=str(e),
                )

        # Fallback to local whisper
        try:
            transcript = await self._transcribe_local(audio_path)
            self.logger.info(
                "Transcription complete (local whisper)",
                length=len(transcript),
            )
            return transcript
        except Exception as e:
            self.logger.error("All transcription methods failed", error=str(e))
            raise RuntimeError(
                f"Transcription failed for {audio_path}: {e}"
            ) from e

    async def _transcribe_nvidia(self, audio_path: str) -> str:
        """
        Transcribe using NVIDIA Whisper API via OpenAI-compatible endpoint.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Transcript text.
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for NVIDIA API transcription. "
                "Install with: pip install openai"
            )

        client = OpenAI(
            api_key=self.nvidia_api_key,
            base_url=self.nvidia_base_url,
        )

        audio = Path(audio_path)

        # NVIDIA Whisper API has a file size limit; chunk if necessary
        file_size_mb = audio.stat().st_size / (1024 * 1024)

        if file_size_mb > 25:
            # Split into chunks and transcribe each
            self.logger.info(
                "Audio file too large for single request, chunking",
                size_mb=round(file_size_mb, 1),
            )
            return await self._transcribe_nvidia_chunked(audio_path, client)

        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="nvidia/parakeet-ctc-1.1b-asr",
                file=f,
                response_format="text",
                language="en",
            )

        if isinstance(response, str):
            return response
        return response.text

    async def _transcribe_nvidia_chunked(
        self, audio_path: str, client
    ) -> str:
        """
        Split a large audio file into chunks and transcribe each via NVIDIA API.

        Args:
            audio_path: Path to the audio file.
            client: OpenAI client configured for NVIDIA.

        Returns:
            Combined transcript text.
        """
        chunks_dir = Path(tempfile.mkdtemp(prefix="jarvis_audio_chunks_"))
        chunk_duration = 600  # 10-minute chunks

        # Split using ffmpeg
        chunk_pattern = str(chunks_dir / "chunk_%03d.wav")
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-f", "segment",
            "-segment_time", str(chunk_duration),
            "-c:a", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            chunk_pattern,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg chunking failed: {proc.stderr}")

        # Transcribe each chunk
        chunks = sorted(chunks_dir.glob("chunk_*.wav"))
        transcripts = []

        for i, chunk in enumerate(chunks):
            self.logger.info(
                f"Transcribing chunk {i + 1}/{len(chunks)}",
                chunk=str(chunk),
            )
            with open(chunk, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="nvidia/parakeet-ctc-1.1b-asr",
                    file=f,
                    response_format="text",
                    language="en",
                )
            text = response if isinstance(response, str) else response.text
            transcripts.append(text.strip())

        # Cleanup chunks
        for chunk in chunks:
            chunk.unlink(missing_ok=True)
        chunks_dir.rmdir()

        return "\n\n".join(transcripts)

    async def _transcribe_local(self, audio_path: str) -> str:
        """
        Transcribe using local whisper model (whisper or faster-whisper).

        Args:
            audio_path: Path to the audio file.

        Returns:
            Transcript text.
        """
        # Try faster-whisper first (much faster on CPU/GPU)
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(
                audio_path, beam_size=5, language="en"
            )
            transcript_parts = [segment.text for segment in segments]
            return " ".join(transcript_parts).strip()
        except ImportError:
            pass

        # Try openai-whisper
        try:
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language="en")
            return result["text"].strip()
        except ImportError:
            pass

        # Try whisper CLI
        try:
            proc = subprocess.run(
                [
                    "whisper", audio_path,
                    "--model", "base",
                    "--language", "en",
                    "--output_format", "txt",
                    "--output_dir", str(Path(audio_path).parent),
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
            if proc.returncode == 0:
                txt_path = Path(audio_path).with_suffix(".txt")
                if txt_path.exists():
                    return txt_path.read_text().strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        raise RuntimeError(
            "No local whisper installation found. Install with: "
            "pip install faster-whisper  OR  pip install openai-whisper"
        )

    async def extract_audio_from_video(
        self, video_path: str, output_audio_path: Optional[str] = None
    ) -> str:
        """
        Extract audio track from a video file using ffmpeg.

        Args:
            video_path: Path to the video file.
            output_audio_path: Optional output path. If None, uses same dir as video.

        Returns:
            Path to the extracted audio file.
        """
        video = Path(video_path)
        if not video.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if output_audio_path is None:
            output_audio_path = str(video.with_suffix(".wav"))

        output = Path(output_audio_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # No video
            "-ac", "1",  # Mono
            "-ar", "16000",  # 16kHz for Whisper
            "-c:a", "pcm_s16le",
            str(output),
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(
                f"Audio extraction failed: {proc.stderr[:500]}"
            )

        self.logger.info(
            "Audio extracted from video",
            video=video_path,
            audio=str(output),
        )
        return str(output)
