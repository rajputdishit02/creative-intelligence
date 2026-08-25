"""Placeholder module for the ReCreate Creative Intelligence MVP."""
import os
from pathlib import Path

from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()


def transcribe_audio(audio_path: str) -> dict:
    audio_file = Path(audio_path)

    if not audio_file.exists():
        return {
            "success": False,
            "transcript": "",
            "words": [],
            "confidence": None,
            "error": f"Audio file does not exist: {audio_file}",
        }

    api_key = os.getenv("DEEPGRAM_API_KEY")

    if not api_key:
        return {
            "success": False,
            "transcript": "",
            "words": [],
            "confidence": None,
            "error": "DEEPGRAM_API_KEY is missing.",
        }

    try:
        client = DeepgramClient(api_key=api_key)

        with open(audio_file, "rb") as file:
            audio_bytes = file.read()

        response = client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="nova-3",
            smart_format=True,
        )

        alternative = response.results.channels[0].alternatives[0]

        transcript = alternative.transcript or ""
        confidence = getattr(alternative, "confidence", None)

        words = []

        if alternative.words:
            for word in alternative.words:
                words.append(
                    {
                        "word": word.word,
                        "start": float(word.start),
                        "end": float(word.end),
                        "confidence": float(word.confidence),
                    }
                )

        return {
            "success": True,
            "transcript": transcript,
            "words": words,
            "confidence": confidence,
            "error": None,
        }

    except Exception as error:
        return {
            "success": False,
            "transcript": "",
            "words": [],
            "confidence": None,
            "error": str(error),
        }