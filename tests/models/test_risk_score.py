import json

import pytest

from src.models.risk_score import (
    _add_diameter_feature,
    _add_encounter_frequency_feature,
    _add_miss_distance_feature,
    _add_velocity_feature,
    _apply_formula,
    _compute_feature_ranges,
    _handle_missing_data,
    _minmax,
    _normalize_features,
    _rank_scores,
    compute_risk_scores,
    explain_score,
    get_weights,
)

# ── Pure helper functions ────────────────────────────────────────────────


def test_minmax_scales_into_zero_one_range():
    assert _minmax(5, 0, 10) == 0.5
    assert _minmax(0, 0, 10) == 0.0
    assert _minmax(10, 0, 10) == 1.0


def test_minmax_handles_zero_range():
    assert _minmax(5, 5, 5) == 0.0


def test_add_diameter_feature_averages_min_and_max():
    rows = [{"estimated_diameter_min_km": 1.0, "estimated_diameter_max_km": 3.0}]
    result = _add_diameter_feature(rows)
    assert result[0]["diameter_km"] == 2.0


def test_add_diameter_feature_handles_missing_values():
    rows = [{"estimated_diameter_min_km": None, "estimated_diameter_max_km": 3.0}]
    result = _add_diameter_feature(rows)
    assert result[0]["diameter_km"] is None


def test_add_velocity_and_miss_distance_and_frequency_features():
    rows = [
        {
            "max_relative_velocity_kps": 12.5,
            "min_miss_distance_km": 1000.0,
            "approach_count": 3,
        }
    ]
    rows = _add_velocity_feature(rows)
    rows = _add_miss_distance_feature(rows)
    rows = _add_encounter_frequency_feature(rows)
    assert rows[0]["velocity_kps"] == 12.5
    assert rows[0]["miss_distance_km"] == 1000.0
    assert rows[0]["encounter_frequency"] == 3


def test_handle_missing_data_marks_scorable_only_when_all_features_present():
    rows = [
        {"diameter_km": 1.0, "velocity_kps": 5.0, "miss_distance_km": 100.0},
        {"diameter_km": 1.0, "velocity_kps": None, "miss_distance_km": 100.0},
        {"diameter_km": None, "velocity_kps": 5.0, "miss_distance_km": None},
    ]
    result = _handle_missing_data(rows)
    assert [r["is_scorable"] for r in result] == [True, False, False]


def test_compute_feature_ranges_excludes_non_scorable_rows():
    rows = [
        {
            "is_scorable": True,
            "diameter_km": 1.0,
            "velocity_kps": 10.0,
            "miss_distance_km": 100.0,
            "encounter_frequency": 1,
        },
        {
            "is_scorable": True,
            "diameter_km": 3.0,
            "velocity_kps": 20.0,
            "miss_distance_km": 300.0,
            "encounter_frequency": 3,
        },
        {
            "is_scorable": False,
            "diameter_km": None,
            "velocity_kps": None,
            "miss_distance_km": None,
            "encounter_frequency": 0,
        },
    ]
    ranges = _compute_feature_ranges(rows)
    assert ranges["diameter_km"] == {"min": 1.0, "max": 3.0}
    assert ranges["velocity_kps"] == {"min": 10.0, "max": 20.0}
    assert ranges["miss_distance_km"] == {"min": 100.0, "max": 300.0}
    assert ranges["encounter_frequency"] == {"min": 1, "max": 3}


def test_normalize_features_inverts_miss_distance():
    rows = [
        {
            "is_scorable": True,
            "diameter_km": 2.0,
            "velocity_kps": 15.0,
            "miss_distance_km": 100.0,
            "encounter_frequency": 2,
        }
    ]
    ranges = {
        "diameter_km": {"min": 1.0, "max": 3.0},
        "velocity_kps": {"min": 10.0, "max": 20.0},
        "miss_distance_km": {"min": 100.0, "max": 300.0},
        "encounter_frequency": {"min": 1, "max": 3},
    }
    result = _normalize_features(rows, ranges)
    row = result[0]
    assert row["diameter_norm"] == pytest.approx(0.5)
    assert row["velocity_norm"] == pytest.approx(0.5)
    # Closest recorded miss distance (100, the range minimum) should be the
    # highest-risk value after inversion.
    assert row["miss_distance_norm"] == pytest.approx(1.0)
    assert row["encounter_frequency_norm"] == pytest.approx(0.5)


def test_normalize_features_sets_none_for_non_scorable_rows():
    rows = [{"is_scorable": False}]
    result = _normalize_features(rows, {})
    row = result[0]
    assert row["diameter_norm"] is None
    assert row["velocity_norm"] is None
    assert row["miss_distance_norm"] is None
    assert row["encounter_frequency_norm"] is None


def test_apply_formula_combines_weighted_contributions():
    rows = [
        {
            "is_scorable": True,
            "diameter_norm": 1.0,
            "miss_distance_norm": 0.0,
            "velocity_norm": 0.0,
            "encounter_frequency_norm": 0.0,
        }
    ]
    result = _apply_formula(rows)
    weights = get_weights()
    assert result[0]["risk_score"] == pytest.approx(weights["size"])


def test_apply_formula_sets_none_for_non_scorable_rows():
    rows = [{"is_scorable": False}]
    result = _apply_formula(rows)
    assert result[0]["risk_score"] is None


def test_rank_scores_orders_descending_and_excludes_non_scorable():
    rows = [
        {"is_scorable": True, "risk_score": 0.2},
        {"is_scorable": True, "risk_score": 0.8},
        {"is_scorable": False, "risk_score": None},
    ]
    result = _rank_scores(rows)
    ranks = [(r["risk_score"], r["rank"]) for r in result]
    assert ranks == [(0.8, 1), (0.2, 2), (None, None)]


# ── get_weights ──────────────────────────────────────────────────────────


def test_get_weights_matches_weights_json():
    weights = get_weights()
    assert weights == {"size": 0.4, "proximity": 0.3, "velocity": 0.2, "frequency": 0.1}
    assert sum(weights.values()) == pytest.approx(1.0)


def test_get_weights_falls_back_to_defaults_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.models.risk_score._WEIGHTS_PATH", tmp_path / "missing_weights.json"
    )
    weights = get_weights()
    assert weights == {
        "size": 0.40,
        "proximity": 0.30,
        "velocity": 0.20,
        "frequency": 0.10,
    }


def test_get_weights_raises_when_weights_do_not_sum_to_one(monkeypatch, tmp_path):
    bad_weights_path = tmp_path / "weights.json"
    bad_weights_path.write_text(
        json.dumps({"size": 0.5, "proximity": 0.3, "velocity": 0.2, "frequency": 0.2})
    )
    monkeypatch.setattr("src.models.risk_score._WEIGHTS_PATH", bad_weights_path)

    with pytest.raises(ValueError, match="sum to 1.0"):
        get_weights()


def test_get_weights_raises_when_keys_missing(monkeypatch, tmp_path):
    bad_weights_path = tmp_path / "weights.json"
    bad_weights_path.write_text(json.dumps({"size": 1.0}))
    monkeypatch.setattr("src.models.risk_score._WEIGHTS_PATH", bad_weights_path)

    with pytest.raises(ValueError, match="missing required keys"):
        get_weights()


# ── Integration: full pipeline against a seeded database ───────────────────


def test_compute_risk_scores_end_to_end(seeded_conn):
    results = {row["asteroid_id"]: row for row in compute_risk_scores(seeded_conn)}

    assert set(results) == {"2000433", "3600001", "3600002", "3600003"}

    # 3600003 has no close approaches recorded — not scorable.
    assert results["3600003"]["is_scorable"] is False
    assert results["3600003"]["risk_score"] is None
    assert results["3600003"]["rank"] is None

    # The other three are scorable, ranked by descending risk score.
    for aid in ("2000433", "3600001", "3600002"):
        assert results[aid]["is_scorable"] is True

    assert results["2000433"]["risk_score"] == pytest.approx(0.400000, abs=1e-5)
    assert results["3600001"]["risk_score"] == pytest.approx(0.509266, abs=1e-5)
    assert results["3600002"]["risk_score"] == pytest.approx(0.465553, abs=1e-5)

    assert results["3600001"]["rank"] == 1
    assert results["3600002"]["rank"] == 2
    assert results["2000433"]["rank"] == 3

    # 3600002 aggregates two close approaches: closest distance and fastest velocity win.
    assert results["3600002"]["miss_distance_km"] == 900_000.0
    assert results["3600002"]["velocity_kps"] == 12.4
    assert results["3600002"]["encounter_frequency"] == 2


def test_explain_score_breaks_down_contributions(seeded_conn):
    results = {row["asteroid_id"]: row for row in compute_risk_scores(seeded_conn)}

    explanation = explain_score(results["2000433"])
    assert explanation["risk_score"] == pytest.approx(0.4, abs=1e-5)
    assert explanation["weights"] == get_weights()
    assert explanation["contributions"]["size"] == pytest.approx(0.4, abs=1e-5)
    assert explanation["contributions"]["proximity"] == pytest.approx(0.0, abs=1e-5)
    assert sum(explanation["contributions"].values()) == pytest.approx(
        explanation["risk_score"], abs=1e-5
    )


def test_explain_score_returns_none_fields_for_non_scorable_asteroid(seeded_conn):
    results = {row["asteroid_id"]: row for row in compute_risk_scores(seeded_conn)}

    explanation = explain_score(results["3600003"])
    assert explanation["is_scorable"] is False
    assert explanation["risk_score"] is None
    assert explanation["weights"] is None
    assert explanation["normalized"] is None
    assert explanation["contributions"] is None
