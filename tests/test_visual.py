import cv2
import numpy as np

from src.analysis.visual import analyse_motion_intensity, analyse_visual_quality


def _solid_frame(value: int) -> np.ndarray:
    return np.full((120, 160, 3), value, dtype=np.uint8)


def _checkerboard() -> np.ndarray:
    board = np.indices((120, 160)).sum(axis=0) % 2
    gray = (board * 255).astype(np.uint8)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def _gradient() -> np.ndarray:
    row = np.linspace(40, 210, 160, dtype=np.uint8)
    gray = np.tile(row, (120, 1))
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def test_dark_frames_are_flagged_as_underexposed_or_near_black():
    result = analyse_visual_quality([_solid_frame(5), _solid_frame(10)])

    assert result["exposure_score"] < 50
    assert any("near-black" in warning for warning in result["warnings"])


def test_bright_frames_are_flagged_as_overexposed():
    result = analyse_visual_quality([_solid_frame(252), _solid_frame(250)])

    assert result["exposure_score"] < 50
    assert any("overexposed" in warning for warning in result["warnings"])


def test_blurred_frames_score_lower_than_sharp_frames():
    sharp_frame = _checkerboard()
    blurred_frame = cv2.GaussianBlur(sharp_frame, (21, 21), 0)

    sharp_result = analyse_visual_quality([sharp_frame])
    blurred_result = analyse_visual_quality([blurred_frame])

    assert sharp_result["sharpness_score"] > blurred_result["sharpness_score"]
    assert blurred_result["sharpness_score"] < 50


def test_low_contrast_scores_below_normal_contrast():
    low_contrast = _solid_frame(120)
    normal_contrast = _gradient()

    low_result = analyse_visual_quality([low_contrast])
    normal_result = analyse_visual_quality([normal_contrast])

    assert low_result["contrast_score"] < 50
    assert normal_result["contrast_score"] > low_result["contrast_score"]


def test_empty_or_missing_frame_input_returns_not_available():
    result = analyse_visual_quality([])

    assert result["score"] == 0
    assert result["label"] == "Not available"
    assert result["warnings"]


def test_motion_intensity_detects_static_frame_sequence():
    frame = _gradient()

    result = analyse_motion_intensity(frame_inputs=[frame, frame.copy(), frame.copy()])

    assert result["motion_level"] == "Visually static"
    assert result["warnings"]
