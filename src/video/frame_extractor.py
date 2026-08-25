"""Keyframe extraction for the Creative Intelligence Platform."""
from pathlib import Path
import cv2


def extract_keyframes(
    video_path: str,
    output_dir: str,
    frame_count: int = 5
) -> list:

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        raise ValueError("Unable to open video for frame extraction.")

    total_frames = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    fps = capture.get(cv2.CAP_PROP_FPS)

    if total_frames <= 0:
        capture.release()
        raise ValueError("Video contains no readable frames.")

    # Choose evenly spaced positions throughout the video.
    positions = [
        int(i * (total_frames - 1) / (frame_count - 1))
        for i in range(frame_count)
    ] if frame_count > 1 else [0]

    extracted_frames = []

    for index, frame_position in enumerate(positions):

        capture.set(
            cv2.CAP_PROP_POS_FRAMES,
            frame_position
        )

        success, frame = capture.read()

        if not success:
            continue

        timestamp = (
            frame_position / fps
            if fps > 0
            else 0
        )

        filename = (
            f"keyframe_{index + 1}_"
            f"{timestamp:.2f}s.jpg"
        )

        filepath = output_path / filename

        cv2.imwrite(
            str(filepath),
            frame
        )

        extracted_frames.append(
            {
                "path": str(filepath),
                "timestamp": round(timestamp, 2),
                "frame_number": frame_position,
            }
        )

    capture.release()

    return extracted_frames
