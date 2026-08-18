from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.core import constants as c
from wa_setpieces.core.penalties import penalty_placement_detail, penalty_taker_summary

DATA = Path(__file__).parent / "data" / "sample_match.json"


def _penalty(event_id, type_id, contestant_id, player_id, player_name, goal_y=None, goal_z=None):
    row = dict(
        eventId=event_id, typeId=type_id, periodId=1, timeMin=10, timeSec=event_id,
        contestantId=contestant_id, playerId=player_id, playerName=player_name,
        outcome=1, x=88.0, y=50.0, q_9=True,
    )
    if goal_y is not None:
        row["q_102"] = goal_y
    if goal_z is not None:
        row["q_103"] = goal_z
    return row


@pytest.fixture
def penalty_events():
    return pd.DataFrame([
        _penalty(1, c.TYPE_GOAL, "A", "p1", "Taker One", goal_y=48.0, goal_z=10.0),
        _penalty(2, c.TYPE_ATTEMPT_SAVED, "A", "p1", "Taker One", goal_y=52.0, goal_z=5.0),
        _penalty(3, c.TYPE_MISS, "B", "p2", "Taker Two", goal_y=30.0, goal_z=40.0),
        _penalty(4, c.TYPE_POST, "B", "p2", "Taker Two"),  # no placement qualifiers
    ])


def test_sample_match_has_no_penalties_returns_empty_with_columns():
    events = load_events(DATA).events
    detail = penalty_placement_detail(events)
    assert detail.empty
    assert list(detail.columns) == [
        "eventId", "contestantId", "playerId", "playerName", "result",
        "goal_y_norm", "goal_h_norm", "corner_zone", "placement_score",
    ]
    summary = penalty_taker_summary(events)
    assert summary.empty


def test_penalty_placement_detail_one_row_per_penalty(penalty_events):
    detail = penalty_placement_detail(penalty_events)
    assert len(detail) == 4
    assert detail["result"].tolist() == ["scored", "saved", "missed", "post"]


def test_penalty_placement_detail_zone_within_grid_when_present(penalty_events):
    detail = penalty_placement_detail(penalty_events)
    with_placement = detail.dropna(subset=["goal_y_norm"])
    assert len(with_placement) == 3
    assert with_placement["corner_zone"].between(0, 8).all()


def test_penalty_placement_detail_missing_qualifiers_is_nan(penalty_events):
    detail = penalty_placement_detail(penalty_events)
    last = detail.iloc[3]
    assert pd.isna(last["goal_y_norm"])
    assert last["corner_zone"] == -1


def test_penalty_taker_summary_conversion_rate(penalty_events):
    summary = penalty_taker_summary(penalty_events).set_index("playerId")
    assert summary.loc["p1", "attempts"] == 2
    assert summary.loc["p1", "goals"] == 1
    assert summary.loc["p1", "conversion_rate"] == 0.5
    assert summary.loc["p2", "attempts"] == 2
    assert summary.loc["p2", "goals"] == 0
    assert summary.loc["p2", "missed"] == 1
    assert summary.loc["p2", "post"] == 1


def test_goal_placement_shared_between_shot_value_and_penalties():
    # core.placement.goal_placement is the shared, refactored-out source
    # of truth; ml.shot_value re-exports the same function as _goal_placement
    # for backward compatibility rather than keeping a second copy.
    pytest.importorskip("xgboost")
    from wa_setpieces.core.placement import goal_placement
    from wa_setpieces.ml.shot_value import _goal_placement

    assert _goal_placement is goal_placement
