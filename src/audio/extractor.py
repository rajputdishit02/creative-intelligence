"""Placeholder module for the ReCreate Creative Intelligence MVP."""
from pathlib import Path
import subprocess
import shutil


def extract_audio(video_path: str, output_dir: str) -> dict:
    video = Path(video_path)
    output = Path(output_dir)

    output.mkdir(parents=True, exist_ok=True)

    audio_path = output / f"{video.stem}.wav"

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": "FFmpeg could not be found by the Python process.",
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
