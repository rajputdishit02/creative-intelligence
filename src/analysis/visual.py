from pathlib import Path

import cv2
import numpy as np


def _label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Needs work"


def _score_from_range(value: float, ranges: list[tuple[float, int]]) -> int:
    for threshold, score in ranges:
        if value >= threshold:
            return score
    return 0


def _load_frame(frame_input) -> np.ndarray | None:
    if isinstance(frame_input, np.ndarray):
        return frame_input

    if isinstance(frame_input, dict):
        frame_input = frame_input.get("path")

    if not frame_input:
        return None

    path = Path(frame_input)

    if not path.exists():
        return None

    return cv2.imread(str(path))


def _normalise_frame(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame

    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def _frame_metrics(frame: np.ndarray) -> dict:
    gray = _normalise_frame(frame)

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    overexposed_ratio = float(np.mean(gray >= 245))
    underexposed_ratio = float(np.mean(gray <= 10))
    near_black = brightness < 20 and contrast < 12

    return {
        "brightness": brightness,
        "contrast": contrast,
        "sharpness": sharpness,
        "overexposed_ratio": overexposed_ratio,
        "underexposed_ratio": underexposed_ratio,
        "near_black": near_black,
    }


def _sharpness_score(sharpness: float) -> int:
    return _score_from_range(
        sharpness,
        [
            (180, 100),
            (100, 85),
            (50, 65),
            (20, 40),
            (1, 20),
        ],
    )


def _contrast_score(contrast: float) -> int:
    return _score_from_range(
        contrast,
        [
            (50, 100),
            (35, 85),
            (25, 70),
            (15, 45),
            (5, 20),
        ],
    )


def _exposure_score(metrics: dict) -> int:
    brightness = metrics["brightness"]
    score = 100

    if brightness < 35:
        score -= 65
    elif brightness < 60:
        score -= 35
    elif brightness < 80:
        score -= 15
    elif brightness > 230:
        score -= 65
    elif brightness > 205:
        score -= 35
    elif brightness > 185:
        score -= 15

    score -= int(metrics["overexposed_ratio"] * 100)
    score -= int(metrics["underexposed_ratio"] * 100)

    return max(0, min(100, score))


def _consistency_score(metrics: list[dict]) -> tuple[int, list[str]]:
    if len(metrics) < 2:
        return 80, ["Only one sampled frame was available, so consistency is estimated conservatively."]

    brightness_values = np.array(
        [metric["brightness"] for metric in metrics],
        dtype=np.float64,
    )
    contrast_values = np.array(
        [metric["contrast"] for metric in metrics],
        dtype=np.float64,
    )
    sharpness_values = np.array(
        [metric["sharpness"] for metric in metrics],
        dtype=np.float64,
    )

    brightness_variation = float(np.std(brightness_values))
    contrast_variation = float(np.std(contrast_values))
    sharpness_cv = float(np.std(sharpness_values) / (np.mean(sharpness_values) + 1))

    score = 100

    if brightness_variation > 45:
        score -= 35
    elif brightness_variation > 25:
        score -= 20
    elif brightness_variation > 15:
        score -= 10

    if contrast_variation > 25:
        score -= 25
    elif contrast_variation > 15:
        score -= 12

    if sharpness_cv > 1.2:
        score -= 25
    elif sharpness_cv > 0.7:
        score -= 12

    reasons = [
        f"Brightness variation across sampled frames is {brightness_variation:.1f}.",
        f"Contrast variation across sampled frames is {contrast_variation:.1f}.",
    ]

    return max(0, min(100, score)), reasons


def analyse_visual_quality(frame_inputs: list) -> dict:
    """
    Analyse sampled frames with transparent OpenCV/NumPy heuristics.
    """

    frames = [
        frame for frame in (
            _load_frame(frame_input)
            for frame_input in frame_inputs
        )
        if frame is not None
    ]

    if not frames:
        return {
            "score": 0,
            "label": "Not available",
            "sharpness_score": 0,
            "exposure_score": 0,
            "contrast_score": 0,
            "consistency_score": 0,
            "warnings": ["No readable sampled frames were available for visual analysis."],
            "reasons": ["Visual quality could not be scored without extracted keyframes."],
        }

    metrics = [_frame_metrics(frame) for frame in frames]

    sharpness_scores = [
        _sharpness_score(metric["sharpness"])
        for metric in metrics
    ]
    exposure_scores = [
        _exposure_score(metric)
        for metric in metrics
    ]
    contrast_scores = [
        _contrast_score(metric["contrast"])
        for metric in metrics
    ]

    sharpness_score = round(float(np.mean(sharpness_scores)), 1)
    exposure_score = round(float(np.mean(exposure_scores)), 1)
    contrast_score = round(float(np.mean(contrast_scores)), 1)
    consistency_score, consistency_reasons = _consistency_score(metrics)

    score = round(
        sharpness_score * 0.30
        + exposure_score * 0.30
        + contrast_score * 0.20
        + consistency_score * 0.20,
        1,
    )

    average_brightness = float(np.mean([metric["brightness"] for metric in metrics]))
    average_contrast = float(np.mean([metric["contrast"] for metric in metrics]))
    average_sharpness = float(np.mean([metric["sharpness"] for metric in metrics]))
    near_black_count = sum(1 for metric in metrics if metric["near_black"])
    overexposed_count = sum(
        1 for metric in metrics
        if metric["overexposed_ratio"] > 0.20
    )
    underexposed_count = sum(
        1 for metric in metrics
        if metric["underexposed_ratio"] > 0.20
    )
    blurred_count = sum(
        1 for metric in metrics
        if _sharpness_score(metric["sharpness"]) < 50
    )

    warnings = []

    if near_black_count:
        warnings.append(f"{near_black_count} sampled frame(s) are black or near-black.")
    if overexposed_count:
        warnings.append(f"{overexposed_count} sampled frame(s) appear overexposed.")
    if underexposed_count:
        warnings.append(f"{underexposed_count} sampled frame(s) appear underexposed.")
    if blurred_count:
        warnings.append(f"{blurred_count} sampled frame(s) appear soft or blurred.")
    if consistency_score < 70:
        warnings.append("Lighting or image quality varies noticeably across sampled frames.")
    if contrast_score < 50:
        warnings.append("Sampled frames have low visual contrast.")

    reasons = [
        f"Average brightness is {average_brightness:.1f} on a 0-255 scale.",
        f"Average contrast is {average_contrast:.1f} based on grayscale standard deviation.",
        f"Average sharpness is {average_sharpness:.1f} using Laplacian variance.",
        *consistency_reasons,
    ]

    return {
        "score": score,
        "label": _label(score),
        "sharpness_score": sharpness_score,
        "exposure_score": exposure_score,
        "contrast_score": contrast_score,
        "consistency_score": consistency_score,
        "warnings": warnings,
        "reasons": reasons,
    }


def _sample_video_frames(video_path: str, sample_count: int) -> list[np.ndarray]:
    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        return []

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 1:
        capture.release()
        return []

    positions = np.linspace(0, total_frames - 1, sample_count, dtype=int)
    frames = []

    for position in positions:
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(position))
        success, frame = capture.read()

        if success:
            frames.append(frame)

    capture.release()
    return frames


def analyse_motion_intensity(
    video_path: str | None = None,
    frame_inputs: list | None = None,
    sample_count: int = 24,
) -> dict:
    """
    Estimate visual activity from frame-to-frame differences.

    This is separate from scene count and pacing.
    """

    frames = []

    if video_path:
        frames = _sample_video_frames(video_path, sample_count)

    if not frames and frame_inputs:
        frames = [
            frame for frame in (
                _load_frame(frame_input)
                for frame_input in frame_inputs
            )
            if frame is not None
        ]

    if len(frames) < 2:
        return {
            "motion_level": "Not available",
            "average_frame_difference": 0,
            "reasons": ["At least two readable frames are required to estimate visual activity."],
            "warnings": ["Visual activity could not be estimated."],
        }

    differences = []
    previous = None

    for frame in frames:
        gray = cv2.resize(_normalise_frame(frame), (160, 90))

        if previous is not None:
            differences.append(float(np.mean(cv2.absdiff(previous, gray))))

        previous = gray

    average_difference = float(np.mean(differences)) if differences else 0

    if average_difference < 4:
        motion_level = "Visually static"
        reason = "Frame differences are minimal across sampled frames."
    elif average_difference < 12:
        motion_level = "Low movement"
        reason = "Frame differences suggest low visual activity."
    elif average_difference < 28:
        motion_level = "Moderate movement"
        reason = "Frame differences suggest a moderate level of visual change."
    else:
        motion_level = "High movement"
        reason = "Frame differences suggest frequent or substantial visual change."

    warnings = []

    if motion_level == "Visually static":
        warnings.append("The video remains visually static for long periods.")

    return {
        "motion_level": motion_level,
        "average_frame_difference": round(average_difference, 2),
        "reasons": [reason],
        "warnings": warnings,
    }
