from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import all_routine_summaries, load_events, restart_routines, routine_summary

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
