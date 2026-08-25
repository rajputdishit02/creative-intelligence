from src.analysis.cta import analyse_cta
from src.analysis.platform import score_platform_fit
from src.analysis.scoring import calculate_creative_score, score_pacing_for_creative
from src.analysis.technical import score_technical_quality


def _cta_words(start_time):
    return [
        {"word": "please", "start": start_time - 0.2, "end": start_time - 0.1},
        {"word": "buy", "start": start_time, "end": start_time + 0.2},
        {"word": "today", "start": start_time + 0.3, "end": start_time + 0.5},
    ]


def test_cta_timing_categories_use_requested_thresholds():
    assert analyse_cta(_cta_words(34), 100)["cta_position"] == "Early"
    assert analyse_cta(_cta_words(35), 100)["cta_position"] == "Middle"
    assert analyse_cta(_cta_words(65), 100)["cta_position"] == "Middle"
    assert analyse_cta(_cta_words(66), 100)["cta_position"] == "Final section"


def test_technical_quality_returns_weighted_components_and_reasons():
    result = score_technical_quality(
        {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "duration": 30,
            "orientation": "Vertical",
            "aspect_ratio": "9:16",
        }
    )

    assert result["score"] == 100
    assert set(result["components"]) == {
        "resolution",
        "frame_rate",
        "orientation",
        "aspect_ratio",
        "duration",
    }
    assert result["reasons"]


def test_platform_fit_scores_requested_platform():
    result = score_platform_fit(
        {
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "duration": 45,
            "orientation": "Landscape",
            "aspect_ratio": "16:9",
        },
        "Website",
    )

    assert result["platform"] == "Website"
    assert result["score"] == 100
    assert result["label"] == "Excellent"


def test_creative_score_uses_transparent_weights():
    result = calculate_creative_score(
        objective_score=80,
        technical_score=90,
        platform_score=70,
        visual_score=88,
        hook_score=60,
        cta_score=50,
        pacing_score=100,
    )

    assert result["score"] == 77.6
    assert result["weights"]["campaign_objective_fit"] == 0.22
    assert result["weights"]["visual_quality"] == 0.15
    assert sum(result["weights"].values()) == 1
    assert "not a validated" in result["disclaimer"]


def test_pacing_score_maps_existing_labels():
    result = score_pacing_for_creative({"pacing_label": "Fast"})

    assert result["score"] == 90
    assert result["reasons"]
