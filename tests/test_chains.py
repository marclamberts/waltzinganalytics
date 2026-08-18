from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import link_set_piece_shots, load_events, set_piece_goal_summary
from wa_setpieces.core import constants as c

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


def test_eventid_is_not_globally_unique_but_chains_handles_it(events):
    # Regression test: eventId is only unique *within one team's own stream*
    # (both teams number their events 1, 2, 3, ... independently), so a
    # naive index-by-eventId lookup can silently resolve qualifier 55
    # ("related event id") to the *other* team's event of the same number.
    # Confirm the precondition still holds on the sample data, and that
    # link_set_piece_shots doesn't misattribute across it: eventId 483
    # belongs to both teams in this match with very different (x, y).
    dupes = events[events["eventId"] == 483]
    assert len(dupes) == 2
    assert dupes["contestantId"].nunique() == 2

    linked = link_set_piece_shots(events)
    # Every set-piece-linked shot's origin must belong to the *same* team as
    # the shot -- an assist is always played by a teammate.
    attributed = linked[linked["set_piece_type"].notna()]
    tagged_events = events.set_index(["contestantId", "eventId"], drop=False)
    for _, row in attributed.iterrows():
        origin_key = (row["contestantId"], row["set_piece_event_id"])
        assert origin_key in tagged_events.index, (
            f"shot {row['eventId']} attributed to a set piece not found on its own team's stream"
        )


def _event_row(matchId, eventId, typeId, contestantId, x, y, outcome=1, q6=None, q55=None):
    row = dict(
        matchId=matchId, eventId=eventId, typeId=typeId, periodId=1, timeMin=0, timeSec=eventId,
        contestantId=contestantId, playerId=f"p{eventId}", playerName=f"P{eventId}",
        outcome=outcome, x=x, y=y,
    )
    if q6 is not None:
        row["q_6"] = q6
    if q55 is not None:
        row["q_55"] = q55
    return row


def test_eventid_collision_across_matches_does_not_misattribute():
    # Regression test: eventId also resets every match, so a naive
    # (contestantId, eventId) index -- safe within one match -- can still
    # collide *across* matches in a season-combined frame. Match m1's
    # eventId 1 is a real corner; match m2's eventId 1 is an unrelated
    # ordinary pass. m2's goal (assisted by its own eventId 1) must not be
    # attributed to m1's corner just because the numbers match.
    events = pd.DataFrame(
        [
            _event_row("m1", 1, c.TYPE_PASS, "A", 99, 99, q6=True),
            _event_row("m2", 1, c.TYPE_PASS, "A", 40, 40),
            _event_row("m2", 3, c.TYPE_GOAL, "A", 10, 50, q55=1),
        ]
    )
    linked = link_set_piece_shots(events)
    goal = linked.loc[linked["matchId"] == "m2"].iloc[0]
    assert goal["set_piece_type"] is None
