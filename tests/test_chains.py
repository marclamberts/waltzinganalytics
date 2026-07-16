from pathlib import Path

import pytest

from opta_setpieces import link_set_piece_shots, load_events, set_piece_goal_summary
from opta_setpieces import constants as c

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_link_set_piece_shots_covers_every_shot(events):
    linked = link_set_piece_shots(events)
    n_shots = (events["typeId"].isin(c.SHOT_TYPE_IDS)).sum()
    assert len(linked) == n_shots


def test_goals_flagged_correctly(events):
    linked = link_set_piece_shots(events)
    n_goals = (events["typeId"] == c.TYPE_GOAL).sum()
    assert linked["is_goal"].sum() == n_goals == 3  # final score was 1-2


def test_set_piece_goal_summary_is_subset_of_goals(events):
    summary = set_piece_goal_summary(events)
    assert list(summary.columns) == ["contestantId", "set_piece_type", "goals"]
    linked = link_set_piece_shots(events)
    total_sp_goals = linked.loc[linked["is_goal"] & linked["set_piece_type"].notna()].shape[0]
    assert summary["goals"].sum() == total_sp_goals
