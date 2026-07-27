import pytest

from src.dashboard import data_service


def test_get_all_scores_returns_one_row_per_asteroid():
    rows = data_service.get_all_scores()
    assert {r["asteroid_id"] for r in rows} == {"2000433", "3600001", "3600002", "3600003"}


def test_get_asteroid_returns_matching_record():
    row = data_service.get_asteroid("2000433")
    assert row is not None
    assert row["name"] == "433 Eros"


def test_get_asteroid_returns_none_for_unknown_id():
    assert data_service.get_asteroid("does-not-exist") is None


def test_search_asteroids_matches_case_insensitive_substring():
    results = data_service.search_asteroids("eros")
    assert [r["asteroid_id"] for r in results] == ["2000433"]


def test_search_asteroids_returns_empty_list_for_empty_query():
    assert data_service.search_asteroids("") == []


def test_get_rankings_excludes_non_scorable_asteroids():
    rankings = data_service.get_rankings()
    assert {r["asteroid_id"] for r in rankings} == {"2000433", "3600001", "3600002"}
    scores = [r["risk_score"] for r in rankings]
    assert scores == sorted(scores, reverse=True)


def test_get_top_risk_limits_and_orders_results():
    top2 = data_service.get_top_risk(2)
    assert [r["asteroid_id"] for r in top2] == ["3600001", "3600002"]


def test_get_summary_metrics_computes_pho_rate():
    metrics = data_service.get_summary_metrics()
    assert metrics["scorable_count"] == 3
    assert metrics["pho_count"] == 1
    assert metrics["pho_rate"] == pytest.approx(1 / 3)


def test_get_approach_statistics_counts_across_all_asteroids():
    stats = data_service.get_approach_statistics()
    assert stats["total_approaches"] == 4
    assert stats["asteroids_with_approaches"] == 3


def test_get_size_distribution_includes_only_known_diameters():
    sizes = data_service.get_size_distribution()
    assert len(sizes) == 4
    assert 18.0 in sizes


def test_get_risk_distribution_matches_scorable_count():
    distribution = data_service.get_risk_distribution()
    assert len(distribution) == 3


def test_get_score_explanation_for_scorable_asteroid():
    explanation = data_service.get_score_explanation("2000433")
    assert explanation is not None
    assert explanation["risk_score"] == pytest.approx(0.4, abs=1e-5)


def test_get_score_explanation_returns_none_for_non_scorable_asteroid():
    assert data_service.get_score_explanation("3600003") is None


def test_get_close_approaches_returns_sorted_records_for_asteroid():
    approaches = data_service.get_close_approaches("3600002")
    dates = [a["close_approach_date"] for a in approaches]
    assert dates == sorted(dates)
    assert len(approaches) == 2


def test_get_close_approaches_returns_empty_list_when_none_recorded():
    assert data_service.get_close_approaches("3600003") == []


def test_get_all_close_approaches_returns_every_recorded_event():
    assert len(data_service.get_all_close_approaches()) == 4


def test_get_feature_matrix_returns_one_row_per_asteroid():
    features = data_service.get_feature_matrix()
    assert {row["asteroid_id"] for row in features} == {
        "2000433",
        "3600001",
        "3600002",
        "3600003",
    }


def test_get_high_level_metrics_aggregates_across_full_population():
    metrics = data_service.get_high_level_metrics()
    assert metrics["asteroid_count"] == 4
    assert metrics["hazardous_count"] == 1
    assert metrics["approach_count"] == 4
