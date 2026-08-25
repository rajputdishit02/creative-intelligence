"""Scene detection for the Creative Intelligence Platform."""
import cv2


def detect_scenes(video_path: str, threshold: float = 30.0) -> dict:
    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        raise ValueError("Unable to open video for scene detection.")

    fps = capture.get(cv2.CAP_PROP_FPS)

    previous_frame = None
    scene_changes = []
    frame_index = 0

    while True:
        success, frame = capture.read()

        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 180))

        if previous_frame is not None:
            difference = cv2.absdiff(previous_frame, gray)
            mean_difference = difference.mean()

            if mean_difference >= threshold:
                timestamp = frame_index / fps if fps > 0 else 0

                # Avoid counting several adjacent frames
                # as separate scene changes.
                if (
                    not scene_changes
                    or timestamp - scene_changes[-1] >= 0.5
                ):
                    scene_changes.append(round(timestamp, 2))

        previous_frame = gray
        frame_index += 1

    capture.release()

    return {
        "scene_count": len(scene_changes) + 1,
        "scene_changes": scene_changes,
    }
