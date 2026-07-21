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
