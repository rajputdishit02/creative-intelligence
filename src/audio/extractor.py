"""Placeholder module for the ReCreate Creative Intelligence MVP."""
import os
from pathlib import Path
import shutil
import subprocess


def _resolve_ffmpeg_path() -> str | None:
    """Find FFmpeg in PATH or common Windows install locations."""
    resolved = shutil.which("ffmpeg")
    if resolved:
        return resolved

    candidates = [
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\GitHub CLI\ffmpeg.exe"),
        Path(r"C:\Program Files\Gyan.dev\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files (x86)\Gyan.dev\ffmpeg\bin\ffmpeg.exe"),
    ]

    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if entry:
            candidates.append(Path(entry) / "ffmpeg.exe")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def extract_audio(video_path: str, output_dir: str) -> dict:
    video = Path(video_path)
    output = Path(output_dir)

    output.mkdir(parents=True, exist_ok=True)

    audio_path = output / f"{video.stem}.wav"

    ffmpeg_path = _resolve_ffmpeg_path()

    if not ffmpeg_path:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": "FFmpeg could not be found. Install FFmpeg and ensure ffmpeg.exe is on PATH or in a common Windows install directory.",
        }

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(video),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": result.stderr,
        }

    if not audio_path.exists() or audio_path.stat().st_size == 0:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": "No usable audio track was found.",
        }

    return {
        "has_audio": True,
        "audio_path": str(audio_path),
        "error": None,
    }
