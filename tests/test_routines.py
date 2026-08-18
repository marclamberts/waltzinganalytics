from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import (
    SeasonDataset,
    all_routine_summaries,
    analyze_routines,
    load_events,
    restart_routines,
    routine_summary,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.mark.parametrize("kind", ["corner", "free_kick", "throw_in", "goal_kick", "kick_off"])
def test_restart_routines_have_geometry_and_taxonomy(events, kind):
    detail = restart_routines(events, kind)
    assert not detail.empty
    assert {"routine_type", "distance", "progression", "direction", "target_channel", "retained"}.issubset(detail)
    assert detail["routine_type"].notna().all()


def test_corner_routine_categories_match_known_sample(events):
    detail = restart_routines(events, "corner")
    assert len(detail) == 9
    assert "short" in set(detail["routine_type"])
    assert detail["distance"].ge(0).all()


def test_routine_summary_usage_sums_to_one_per_team(events):
    summary = routine_summary(events, "free_kick")
    assert summary.groupby("contestantId")["usage_share"].sum().between(0.999, 1.001).all()
    assert summary["success_rate"].between(0, 1).all()


def test_routine_channel_and_side_match_zones_convention(events):
    # Regression test: routines.py used to define its own private
    # third/channel thresholds with the opposite left/right direction from
    # zones.add_channels' canonical convention (low y = left), so the same
    # delivery could get contradictory flank labels depending on which
    # function was called. It now reuses zones.add_thirds/add_channels
    # directly, so start_channel must agree with add_channels on the same
    # rows, and side/start_channel must agree with each other.
    from wa_setpieces.core.filters import extract_corners
    from wa_setpieces.core.zones import add_channels

    corners = extract_corners(events)
    direct = add_channels(corners, n=5).set_index("eventId")["channel"]
    detail = restart_routines(events, "corner").set_index("eventId")
    assert (detail["start_channel"].astype(str) == direct.loc[detail.index].astype(str)).all()

    low_y = detail["y"] < 40
    assert (detail.loc[low_y, "side"] == "left").all()
    assert (detail.loc[low_y, "start_channel"].isin(["left_wide", "left_half_space"])).all()
    high_y = detail["y"] > 60
    assert (detail.loc[high_y, "side"] == "right").all()
    assert (detail.loc[high_y, "start_channel"].isin(["right_wide", "right_half_space"])).all()


def test_penalty_taxonomy():
    base = {"id": 1, "eventId": 1, "periodId": 1, "timeMin": 10, "timeSec": 0,
            "contestantId": "A", "playerId": "p", "playerName": "Player", "outcome": 1,
            "x": 88.5, "y": 50.0, "timeStamp": None, "q_9": True}
    rows = [{**base, "eventId": i, "typeId": type_id} for i, type_id in enumerate((16, 15, 14, 13), 1)]
    detail = restart_routines(pd.DataFrame(rows), "penalty")
    assert detail["routine_type"].tolist() == ["scored", "saved", "post", "missed"]


def test_all_routine_summaries_contains_supported_sample_types(events):
    summary = all_routine_summaries(events)
    assert {"corner", "free_kick", "throw_in", "goal_kick", "kick_off"}.issubset(set(summary["set_piece_type"]))


def test_structured_analysis_contains_five_coordinated_tables(events):
    analysis = analyze_routines(events, "corner")
    assert analysis.set_piece_type == "corner"
    assert {"distance_m", "angle_degrees", "verticality", "destination_zone", "outcome_category", "routine_key"}.issubset(analysis.detail)
    assert {"routine_diversity", "top_pattern_share", "most_used_pattern"}.issubset(analysis.team_profiles)
    assert {"preferred_routine", "shots_created"}.issubset(analysis.taker_profiles)
    assert {"destination_zone", "team_usage_share"}.issubset(analysis.target_matrix)


def test_multi_match_routines_are_analysed_within_boundaries():
    season = SeasonDataset.from_sources([DATA, DATA], match_ids=["m1", "m2"])
    detail = analyze_routines(season.events, "corner").detail
    assert len(detail) == 18
    assert set(detail["matchId"]) == {"m1", "m2"}
