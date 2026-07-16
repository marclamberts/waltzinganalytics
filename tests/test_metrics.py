from pathlib import Path

import pytest

from wa_setpieces import (
    delivery_locations,
    load_events,
    player_set_piece_counts,
    set_piece_summary,
    team_set_piece_counts,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_team_counts_sum_to_extracted_totals(events):
    counts = team_set_piece_counts(events)
    assert counts["attempts"].sum() == 9 + 25 + 50 + 12 + 4  # corners+fk+throw-ins+goal kicks+kickoffs
    assert set(counts["contestantId"].unique()) == {
        "cxb4hqite921i36gwrezdts7c",
        "f2yd0yzt0om6qhks9gbowu1d6",
    }


def test_success_rate_between_zero_and_one(events):
    counts = team_set_piece_counts(events)
    assert counts["success_rate"].between(0, 1).all()


def test_player_counts_have_names(events):
    counts = player_set_piece_counts(events)
    assert counts["playerName"].notna().all()
    assert (counts["attempts"] > 0).all()


def test_set_piece_summary_has_shots_and_goals_columns(events):
    summary = set_piece_summary(events)
    assert {"shots", "goals", "attempts", "success_rate"}.issubset(summary.columns)
    assert (summary["goals"] <= summary["shots"]).all()
    assert (summary["shots"] <= summary["attempts"]).all()


def test_delivery_locations_for_corners(events):
    corners = delivery_locations(events, "corner")
    assert len(corners) == 9
    assert {"x", "y", "end_x", "end_y"}.issubset(corners.columns)


def test_delivery_locations_rejects_penalty(events):
    with pytest.raises(ValueError):
        delivery_locations(events, "penalty")
