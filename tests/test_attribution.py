import pandas as pd

from wa_setpieces.core import constants as c
from wa_setpieces.core.attribution import first_contact_detail, first_contact_summary


def test_first_contact_detail_finds_the_next_on_ball_event():
    events = pd.DataFrame(
        [
            dict(
                eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=0, timeSec=0,
                contestantId="A", playerId="pA1", playerName="A1", outcome=1,
                x=99.0, y=50.0, q_6=True,
            ),
            dict(
                eventId=2, typeId=c.TYPE_AERIAL, periodId=1, timeMin=0, timeSec=2,
                contestantId="B", playerId="pB1", playerName="B1", outcome=1,
                x=90.0, y=50.0,
            ),
        ]
    )
    detail = first_contact_detail(events, "corner")
    assert len(detail) == 1
    row = detail.iloc[0]
    assert row["first_contact_player_id"] == "pB1"
    assert row["first_contact_team_id"] == "B"
    assert row["first_contact_won"] == False  # noqa: E712
    assert row["seconds_to_contact"] == 2.0
    assert row["confidence"] == "event_sequence"


def test_first_contact_summary_win_rate_between_zero_and_one():
    events = pd.DataFrame(
        [
            dict(
                eventId=1, typeId=c.TYPE_PASS, periodId=1, timeMin=0, timeSec=0,
                contestantId="A", playerId="pA1", playerName="A1", outcome=1,
                x=99.0, y=50.0, q_6=True,
            ),
            dict(
                eventId=2, typeId=c.TYPE_AERIAL, periodId=1, timeMin=0, timeSec=2,
                contestantId="A", playerId="pA2", playerName="A2", outcome=1,
                x=90.0, y=50.0,
            ),
        ]
    )
    summary = first_contact_summary(events, "corner")
    assert (summary["win_rate"].between(0, 1)).all()


def test_first_contact_detail_stays_within_match_boundaries():
    # Regression test: first_contact_detail used to walk the whole events
    # frame by row position with only a periodId check, never matchId, so
    # a delivery near the end of one match could pick up an unrelated
    # event from the start of the next match (clock reset to ~0) as if it
    # were its own next event. m1's corner has no real follow-up at all;
    # m2's first event is an unrelated pass 2 seconds later on the reset
    # clock. Without per-match scoping this corner is misattributed to
    # that event.
    events = pd.DataFrame(
        [
            dict(
                matchId="m1", eventId=1, typeId=c.TYPE_PASS, periodId=1,
                timeMin=0, timeSec=0, contestantId="A", playerId="pA1",
                playerName="A1", outcome=1, x=99.0, y=50.0, q_6=True,
            ),
            dict(
                matchId="m2", eventId=1, typeId=c.TYPE_PASS, periodId=1,
                timeMin=0, timeSec=2, contestantId="B", playerId="pB1",
                playerName="B1", outcome=1, x=50.0, y=50.0,
            ),
        ]
    )
    detail = first_contact_detail(events, "corner")
    assert len(detail) == 1
    row = detail.iloc[0]
    assert row["matchId"] == "m1"
    assert row["first_contact_player_id"] is None
    assert row["seconds_to_contact"] is None
