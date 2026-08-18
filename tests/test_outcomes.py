from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.core import constants as c
from wa_setpieces.core.filters import extract_corners, extract_free_kicks
from wa_setpieces.core.outcomes import (
    OUTCOME_CATEGORIES,
    delivery_outcomes,
    outcome_summary,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_delivery_outcomes_one_row_per_delivery(events):
    corners = delivery_outcomes(events, "corner")
    assert len(corners) == len(extract_corners(events))

    free_kicks = delivery_outcomes(events, "free_kick")
    assert len(free_kicks) == len(extract_free_kicks(events))


def test_delivery_outcomes_rejects_bad_type(events):
    with pytest.raises(ValueError):
        delivery_outcomes(events, "throw_in")


def test_every_category_is_a_known_category(events):
    corners = delivery_outcomes(events, "corner")
    assert corners["category"].isin(OUTCOME_CATEGORIES).all()


def test_no_missing_coordinates(events):
    corners = delivery_outcomes(events, "corner")
    assert corners["x"].notna().all()
    assert corners["y"].notna().all()


def test_coordinates_within_pitch_bounds(events):
    for sp_type in ("corner", "free_kick"):
        outcomes = delivery_outcomes(events, sp_type)
        assert outcomes["x"].between(-5, 105).all()  # small slack for out-of-bounds events
        assert outcomes["y"].between(-5, 105).all()


def test_known_category_counts_for_corners(events):
    # Cross-checked by hand against the raw delivery coordinates for this
    # match: eventId 723 goes (99.7, 99.1) -> (95.7, 89.9), a 10-unit pass
    # that stays tight in the corner area rather than crossing into the
    # box -- a genuine short corner. The rest are normal crosses (30-58
    # units of travel), split between two second-phase shots, one aerial
    # duel, four lost first touches, and one won. (Corner eventId 404's
    # following events -- a cxb4... aerial duel and an f2yd... clearance --
    # share the same rounded timeMin/timeSec; their timeStamp values (which
    # loader.load_events now uses to break exactly this kind of tie, see
    # core/loader.py) show the clearance logged ~0.1s earlier, so it is the
    # true next event and this delivery is a lost first touch, not an
    # aerial duel.)
    corners = delivery_outcomes(events, "corner")
    counts = corners["category"].value_counts().to_dict()
    assert counts == {
        "first_touch_lost": 4,
        "second_phase_shot": 2,
        "aerial_duel": 1,
        "first_touch_won": 1,
        "short_corner": 1,
    }


def test_outcome_summary_matches_detail(events):
    detail = delivery_outcomes(events, "corner")
    summary = outcome_summary(events, "corner")
    assert summary["count"].sum() == len(detail)
    for _, row in summary.iterrows():
        expected = len(
            detail[
                (detail["contestantId"] == row["contestantId"])
                & (detail["category"] == row["category"])
            ]
        )
        assert row["count"] == expected


def test_outcome_summary_empty_events():
    import pandas as pd

    empty = pd.DataFrame(
        columns=[
            "id", "eventId", "typeId", "periodId", "timeMin", "timeSec",
            "contestantId", "playerId", "playerName", "outcome", "x", "y", "timeStamp",
        ]
    )
    summary = outcome_summary(empty, "corner")
    assert summary.empty
    assert list(summary.columns) == ["contestantId", "category", "count"]


def test_short_corner_detection_with_synthetic_data(events):
    from wa_setpieces.core.outcomes import classify_delivery_outcome

    corners = extract_corners(events)
    real_corner = corners.iloc[0].copy()
    # Fabricate a short corner: a small pass along the byline (short
    # distance), the way a real short corner is played -- not a threshold
    # on end position, since a corner starts at x~99-100 already, so even a
    # genuine short corner barely moves x at all (see module docstring).
    real_corner["set_piece_type"] = "corner"
    real_corner["q_140"] = real_corner["x"] - 6  # pass end x
    real_corner["q_141"] = real_corner["y"] + 5  # pass end y
    result = classify_delivery_outcome(events, real_corner)
    assert result["category"] == "short_corner"
    assert result["x"] == pytest.approx(real_corner["x"] - 6)


def test_long_corner_is_not_misclassified_as_short(events):
    from wa_setpieces.core.outcomes import classify_delivery_outcome

    corners = extract_corners(events)
    real_corner = corners.iloc[0].copy()
    real_corner["set_piece_type"] = "corner"
    result = classify_delivery_outcome(events, real_corner)
    # The real deliveries in the sample match are all normal crosses into
    # the box, well beyond the short-corner distance threshold.
    assert result["category"] != "short_corner"


def test_no_action_preserves_falsy_but_valid_end_position():
    from wa_setpieces.core.outcomes import classify_delivery_outcome

    # Regression test: the no_action branch used to fall back with `value or
    # default`, which silently discards a real end position of 0.0 (a valid
    # pitch coordinate right on the touchline/byline) as if it were missing.
    events = pd.DataFrame(
        [
            dict(
                eventId=1, typeId=32, periodId=1, timeMin=0, timeSec=0,
                contestantId="B", playerId="p2", playerName="P2",
                outcome=None, x=50.0, y=50.0,
            ),
            dict(
                eventId=2, typeId=c.TYPE_PASS, periodId=1, timeMin=0, timeSec=1,
                contestantId="A", playerId="p1", playerName="P1", outcome=1,
                x=99.5, y=99.5, q_6=True, q_140=0.0, q_141=0.0,
            ),
        ]
    )
    delivery_row = events.iloc[1].copy()
    delivery_row["set_piece_type"] = "corner"
    result = classify_delivery_outcome(events, delivery_row)
    assert result["category"] == "no_action"
    assert result["x"] == 0.0
    assert result["y"] == 0.0
