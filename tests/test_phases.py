from pathlib import Path

import pytest

from wa_setpieces import load_events
from wa_setpieces.core.filters import extract_corners, extract_free_kicks
from wa_setpieces.core.phases import second_phase_summary, second_phases

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_second_phases_one_row_per_delivery(events):
    corners = second_phases(events, "corner")
    assert len(corners) == len(extract_corners(events))

    free_kicks = second_phases(events, "free_kick")
    assert len(free_kicks) == len(extract_free_kicks(events))


def test_second_phases_rejects_bad_type(events):
    with pytest.raises(ValueError):
        second_phases(events, "throw_in")


def test_second_phase_shot_flags_are_boolean(events):
    corners = second_phases(events, "corner")
    assert corners["second_phase_shot"].isin([True, False]).all()
    assert corners["cleared_immediately"].isin([True, False]).all()


def test_second_phase_finds_known_shots(events):
    # Cross-checked by hand against the raw event stream: corner delivery
    # eventId 610 and eventId 730 are each followed (after an intervening
    # contested touch) by a shot from the same team before the ball is
    # cleared or goes out -- i.e. a genuine second-phase shot.
    corners = second_phases(events, "corner")
    flagged = set(corners.loc[corners["second_phase_shot"], "delivery_event_id"])
    assert flagged == {610, 730}


def test_second_phase_summary_matches_detail(events):
    detail = second_phases(events, "corner")
    summary = second_phase_summary(events, "corner")
    assert summary["deliveries"].sum() == len(detail)
    assert summary["second_phases"].sum() == detail["second_phase_shot"].sum()


def test_phase_window_stops_at_period_boundary():
    # A corner right at the end of period 1, with what would otherwise look
    # like a direct shot moments later by raw clock time -- but that event
    # is in period 2 (second-half kickoff resets the clock near 0, so by
    # elapsed-seconds alone it looks like a same-period follow-up). The
    # window must stop at the period change rather than bleed into the
    # next half, the same class of boundary classify_phase already guards
    # against for match boundaries.
    import pandas as pd

    from wa_setpieces.core import constants as c

    events = pd.DataFrame([
        dict(
            eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=45, timeSec=0,
            contestantId="A", playerId="p1", playerName="Taker", outcome=1,
            x=99.5, y=50.0, q_6=True,
        ),
        dict(
            eventId=2, typeId=c.TYPE_GOAL, periodId=2, timeMin=45, timeSec=2,
            contestantId="A", playerId="p2", playerName="Scorer", outcome=1,
            x=95.0, y=50.0,
        ),
        dict(
            eventId=3, typeId=c.TYPE_PASS, periodId=1, timeMin=0, timeSec=0,
            contestantId="B", playerId="p3", playerName="B1", outcome=1,
            x=50.0, y=50.0,
        ),
    ])
    detail = second_phases(events, "corner")
    assert len(detail) == 1
    row = detail.iloc[0]
    assert row["direct_shot"] == False  # noqa: E712
    assert row["first_contact_event_id"] is None
    assert row["phase_events_n"] == 0


def test_second_phases_rejects_wrong_team_count():
    import pandas as pd

    from wa_setpieces.core import constants as c

    three_teams = pd.DataFrame([
        dict(
            eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=0, timeSec=0,
            contestantId="A", playerId="p1", playerName="Taker", outcome=1,
            x=99.5, y=50.0, q_6=True,
        ),
        dict(
            eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=1, timeSec=0,
            contestantId="B", playerId="p2", playerName="B1", outcome=1,
            x=50.0, y=50.0,
        ),
        dict(
            eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=2, timeSec=0,
            contestantId="C", playerId="p3", playerName="C1", outcome=1,
            x=50.0, y=50.0,
        ),
    ])
    with pytest.raises(ValueError, match="expected exactly 2 teams"):
        second_phases(three_teams, "corner")
