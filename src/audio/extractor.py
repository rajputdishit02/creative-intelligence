import os
from pathlib import Path
import shutil
import subprocess


def _resolve_ffmpeg_path() -> str | None:
    """
    Find FFmpeg on Windows.

    Search order:
    1. System PATH
    2. Common installation folders
    3. WinGet package directory
    """

    # First try the normal system PATH
    resolved = shutil.which("ffmpeg")

    if resolved:
        return resolved

    candidates = [
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\Gyan.dev\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files (x86)\Gyan.dev\ffmpeg\bin\ffmpeg.exe"),
    ]

    # Search every directory currently present in PATH
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if entry:
            candidates.append(
                Path(entry) / "ffmpeg.exe"
            )

    # Winget commonly installs FFmpeg here
    local_appdata = os.environ.get("LOCALAPPDATA")

    if local_appdata:
        winget_packages = (
            Path(local_appdata)
            / "Microsoft"
            / "WinGet"
            / "Packages"
        )

        if winget_packages.exists():
            try:
                candidates.extend(
                    winget_packages.rglob("ffmpeg.exe")
                )
            except OSError:
                pass

    # Return the first valid FFmpeg executable
    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        except OSError:
            continue

    return None


def extract_audio(video_path: str, output_dir: str) -> dict:
    """
    Extract mono 16 kHz WAV audio from a video.

    Returns:
        {
            "has_audio": bool,
            "audio_path": str | None,
            "error": str | None
        }
    """

    video = Path(video_path)
    output = Path(output_dir)

    if not video.exists():
        return {
            "has_audio": False,
            "audio_path": None,
            "error": f"Video file does not exist: {video}",
        }

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    audio_path = output / f"{video.stem}.wav"

    ffmpeg_path = _resolve_ffmpeg_path()

    if not ffmpeg_path:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": (
                "FFmpeg could not be found. "
                "The application searched PATH, common Windows "
                "locations, and the WinGet package directory."
            ),
        }

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(video),

        # Do not copy video
        "-vn",

        # WAV format suitable for speech recognition
        "-acodec",
        "pcm_s16le",

        # Whisper-friendly sample rate
        "-ar",
        "16000",

        # Mono audio
        "-ac",
        "1",

        str(audio_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": (
                f"FFmpeg executable could not be started: "
                f"{ffmpeg_path}"
            ),
        }

    except Exception as error:
        return {
            "has_audio": False,
            "audio_path": None,
            "error": str(error),
        }

    # FFmpeg returns a non-zero code when the video
    # contains no usable audio stream.
    if result.returncode != 0:

        error_message = result.stderr or "FFmpeg audio extraction failed."

        # Give a cleaner message when no audio stream exists
        lower_error = error_message.lower()

        if (
            "does not contain any stream" in lower_error
            or "matches no streams" in lower_error
            or "audio" in lower_error
            and "stream" in lower_error
        ):
            return {
                "has_audio": False,
                "audio_path": None,
                "error": "The video does not appear to contain a usable audio track.",
            }

        return {
            "has_audio": False,
            "audio_path": None,
            "error": error_message,
        }

    if (
        not audio_path.exists()
        or audio_path.stat().st_size == 0
    ):
        return {
            "has_audio": False,
            "audio_path": None,
            "error": "No usable audio track was extracted.",
        }

    return {
        "has_audio": True,
        "audio_path": str(audio_path),
        "error": None,
    }