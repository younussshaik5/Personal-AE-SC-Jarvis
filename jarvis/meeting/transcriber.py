#!/usr/bin/env python3
"""
Meeting transcription using NVIDIA ASR API (OpenAI-compatible endpoint)
with local whisper fallback.

Key improvements over v1:
- Parallel chunk transcription (asyncio.gather + semaphore)
- 30s overlap between chunks to prevent boundary word loss
- Dynamic timeouts based on file size
- Retry with exponential backoff on transient API errors
- Configurable model name from jarvis.yaml
"""

import asyncio
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.retry import retry


class MeetingTranscriber:
    """Transcribes meeting audio using NVIDIA ASR API or local whisper."""

    def __init__(
        self,
        nvidia_api_key: str,
        nvidia_base_url: str,
        model: str = "nvidia/parakeet-ctc-1.1b-asr",
        chunk_duration: int = 600,
        chunk_overlap: int = 30,
        max_parallel: int = 5,
        ffmpeg_timeout_per_gb: int = 600,
    ):
        self.nvidia_api_key = nvidia_api_key
        self.nvidia_base_url = nvidia_base_url.rstrip("/")
        self.model = model
        self.chunk_duration = chunk_duration
        self.chunk_overlap = chunk_overlap
        self.max_parallel = max_parallel
        self.ffmpeg_timeout_per_gb = ffmpeg_timeout_per_gb
        self.logger = JARVISLogger("meeting.transcriber")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

    async def extract_audio_from_video(
        self, video_path: str, output_audio_path: Optional[str] = None
    ) -> str:
        """
        Extract audio track from a video file using ffmpeg.
        Dynamic timeout based on file size.

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
            "-vn",            # No video
            "-ac", "1",       # Mono
            "-ar", "16000",   # 16kHz for Whisper
            "-c:a", "pcm_s16le",
            str(output),
        ]

        timeout = self._get_ffmpeg_timeout(video_path)
        self.logger.info(
            "Extracting audio from video",
            video=video_path,
            timeout_seconds=timeout,
        )

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(
                f"Audio extraction timed out after {timeout}s for {video_path}"
            )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Audio extraction failed: {stderr.decode()[:500]}"
            )

        self.logger.info(
            "Audio extracted from video",
            video=video_path,
            audio=str(output),
        )
        return str(output)

    # ------------------------------------------------------------------
    # NVIDIA transcription
    # ------------------------------------------------------------------

    async def _transcribe_nvidia(self, audio_path: str) -> str:
        """
        Transcribe using NVIDIA ASR API via OpenAI-compatible endpoint.
        Files >25 MB are chunked and transcribed in parallel with overlap.
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
        file_size_mb = audio.stat().st_size / (1024 * 1024)

        if file_size_mb > 25:
            self.logger.info(
                "Audio file too large for single request, chunking with parallel transcription",
                size_mb=round(file_size_mb, 1),
            )
            return await self._transcribe_nvidia_chunked(audio_path, client)

        # Single-shot for files <= 25 MB
        @retry(max_attempts=3, backoff_base=2.0)
        async def _single_shot(path: str) -> str:
            with open(path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    response_format="text",
                    language="en",
                )
            return response if isinstance(response, str) else response.text

        return await _single_shot(audio_path)

    async def _transcribe_nvidia_chunked(
        self, audio_path: str, client
    ) -> str:
        """
        Split a large audio file into overlapping chunks and transcribe
        each in parallel via NVIDIA API.

        Chunk layout (with 30s overlap):
          chunk_000: 0:00  - 10:00
          chunk_001: 9:30  - 20:00  (30s overlap with chunk_000)
          chunk_002: 19:30 - 30:00  (30s overlap with chunk_001)
          ...
        """
        chunks_dir = Path(tempfile.mkdtemp(prefix="jarvis_audio_chunks_"))
        duration = self.chunk_duration
        overlap = self.chunk_overlap

        try:
            # Get total audio duration
            total_duration = await self._get_audio_duration(audio_path)

            # Generate chunk boundaries with overlap
            chunk_specs = []
            start = 0
            while start < total_duration:
                end = min(start + duration, total_duration)
                chunk_specs.append((start, end))
                start += duration - overlap

            self.logger.info(
                "Splitting audio into overlapping chunks",
                total_duration_s=round(total_duration),
                chunk_count=len(chunk_specs),
                chunk_duration_s=duration,
                overlap_s=overlap,
            )

            # Extract chunks with ffmpeg (sequential — I/O bound, not worth parallelizing)
            chunk_paths = []
            for i, (chunk_start, chunk_end) in enumerate(chunk_specs):
                chunk_path = chunks_dir / f"chunk_{i:03d}.wav"
                chunk_dur = chunk_end - chunk_start
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(chunk_start),
                    "-i", audio_path,
                    "-t", str(chunk_dur),
                    "-c:a", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    str(chunk_path),
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"ffmpeg chunk extraction failed for chunk {i}: "
                        f"{stderr.decode()[:300]}"
                    )
                chunk_paths.append((chunk_path, chunk_start))

            # Transcribe all chunks in parallel with bounded concurrency
            semaphore = asyncio.Semaphore(self.max_parallel)
            self.logger.info(
                "Transcribing chunks in parallel",
                chunks=len(chunk_paths),
                max_concurrent=self.max_parallel,
            )

            async def _transcribe_chunk(chunk_info):
                chunk_path, chunk_start = chunk_info
                async with semaphore:
                    text = await self._transcribe_single_chunk(client, str(chunk_path))
                    return (chunk_start, text)

            results = await asyncio.gather(
                *[_transcribe_chunk(ci) for ci in chunk_paths],
                return_exceptions=True,
            )

            # Separate successes from failures
            transcripts = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Chunk {i} transcription failed",
                        error=str(result),
                    )
                    # Insert placeholder so ordering is preserved
                    transcripts.append((chunk_specs[i][0], "[CHUNK TRANSCRIPTION FAILED]"))
                else:
                    transcripts.append(result)

            # Sort by start time and merge with overlap deduplication
            transcripts.sort(key=lambda x: x[0])
            merged = self._merge_with_overlap_dedup(
                [t[1] for t in transcripts],
                overlap_seconds=overlap,
            )

            return merged

        finally:
            # Cleanup chunks
            try:
                shutil.rmtree(chunks_dir, ignore_errors=True)
            except Exception:
                pass

    async def _transcribe_single_chunk(self, client, chunk_path: str) -> str:
        """Transcribe a single audio chunk with retry."""

        @retry(max_attempts=3, backoff_base=2.0)
        async def _do_transcribe(path: str) -> str:
            with open(path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    response_format="text",
                    language="en",
                )
            return response if isinstance(response, str) else response.text

        return await _do_transcribe(chunk_path)

    def _merge_with_overlap_dedup(
        self, transcripts: List[str], overlap_seconds: int
    ) -> str:
        """
        Merge chunk transcripts, removing duplicate text from overlapping regions.

        For each pair of adjacent chunks, find the longest common substring
        at the boundary and trim the overlap.
        """
        if not transcripts:
            return ""
        if len(transcripts) == 1:
            return transcripts[0].strip()

        merged = transcripts[0].strip()

        for i in range(1, len(transcripts)):
            current = transcripts[i].strip()
            if not current:
                continue
            if not merged:
                merged = current
                continue

            # Try to find overlap: take last N words of merged, first N words of current
            # N proportional to overlap_seconds (roughly 3-4 words per second)
            max_overlap_words = max(10, overlap_seconds * 3)

            merged_words = merged.split()
            current_words = current.split()

            search_len = min(max_overlap_words, len(merged_words), len(current_words))

            best_overlap = 0
            for n in range(search_len, 0, -1):
                if merged_words[-n:] == current_words[:n]:
                    best_overlap = n
                    break

            if best_overlap > 0:
                # Trim duplicate words from current
                merged = merged + " " + " ".join(current_words[best_overlap:])
            else:
                # No overlap found — join with separator
                merged = merged + "\n\n" + current

        return merged

    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except (ValueError, TypeError):
            # Fallback: estimate from file size (rough: 16kHz mono WAV = 32KB/s)
            return Path(audio_path).stat().st_size / 32000

    # ------------------------------------------------------------------
    # Local whisper fallback
    # ------------------------------------------------------------------

    async def _transcribe_local(self, audio_path: str) -> str:
        """
        Transcribe using local whisper model.
        Tries: faster-whisper (medium) → openai-whisper (medium) → whisper CLI (base).
        """
        # Try faster-whisper first (much faster on CPU/GPU)
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("medium", device="cpu", compute_type="int8")
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

            model = whisper.load_model("medium")
            result = model.transcribe(audio_path, language="en")
            return result["text"].strip()
        except ImportError:
            pass

        # Try whisper CLI (base model as last resort)
        try:
            proc = await asyncio.create_subprocess_exec(
                "whisper", audio_path,
                "--model", "base",
                "--language", "en",
                "--output_format", "txt",
                "--output_dir", str(Path(audio_path).parent),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=600)
            except asyncio.TimeoutError:
                proc.kill()
                raise RuntimeError("Whisper CLI timed out after 600s")

            if proc.returncode == 0:
                txt_path = Path(audio_path).with_suffix(".txt")
                if txt_path.exists():
                    text = txt_path.read_text().strip()
                    txt_path.unlink(missing_ok=True)
                    return text
        except FileNotFoundError:
            pass

        raise RuntimeError(
            "No local whisper installation found. Install with: "
            "pip install faster-whisper  OR  pip install openai-whisper"
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _get_ffmpeg_timeout(self, file_path: str) -> int:
        """Dynamic timeout based on file size: min 300s, +600s per GB."""
        try:
            size_gb = Path(file_path).stat().st_size / (1024 ** 3)
        except Exception:
            size_gb = 1.0
        return max(300, int(size_gb * self.ffmpeg_timeout_per_gb))
