"""Video metadata extraction for the Creative Intelligence Platform."""
from pathlib import Path
import cv2


def analyse_video(video_path: str) -> dict:
    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    capture = cv2.VideoCapture(str(path))

    if not capture.isOpened():
        raise ValueError("Unable to open the uploaded video.")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    capture.release()

    duration = frame_count / fps if fps > 0 else 0

    if width > height:
        orientation = "Landscape"
    elif height > width:
        orientation = "Vertical"
    else:
        orientation = "Square"

    aspect_ratio_decimal = width / height if height > 0 else 0

    common_ratios = {
        (9, 16): 9 / 16,
        (16, 9): 16 / 9,
        (1, 1): 1,
        (4, 5): 4 / 5,
        (3, 4): 3 / 4,
    }

    aspect_ratio = f"{aspect_ratio_decimal:.2f}:1"

    for ratio_name, ratio_value in common_ratios.items():
        if abs(aspect_ratio_decimal - ratio_value) < 0.03:
            aspect_ratio = f"{ratio_name[0]}:{ratio_name[1]}"
            break

    file_size_mb = path.stat().st_size / (1024 * 1024)

    return {
        "duration": round(duration, 2),
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "resolution": f"{width} × {height}",
        "frame_count": frame_count,
        "aspect_ratio": aspect_ratio,
        "orientation": orientation,
        "file_size_mb": round(file_size_mb, 2),
    }
