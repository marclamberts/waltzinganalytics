from pathlib import Path

import pytest

from opta_setpieces import load_events
from opta_setpieces.retention import retention_detail, retention_rate

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_retention_rejects_penalty(events):
    with pytest.raises(ValueError):
        retention_detail(events, "penalty")


@pytest.mark.parametrize(
    "set_piece_type", ["corner", "free_kick", "throw_in", "goal_kick", "kick_off"]
)
def test_retention_detail_covers_every_delivery(events, set_piece_type):
    from opta_setpieces.filters import extract_all

    detail = retention_detail(events, set_piece_type)
    assert len(detail) == len(extract_all(events)[set_piece_type])
    assert detail["retained"].isin([True, False, None]).all()


def test_retention_diverges_from_raw_outcome(events):
    # Retention (still in possession N seconds later) is a broader signal
    # than the raw pass "outcome" flag -- there should be at least one
    # corner where they disagree (e.g. a flick-on that isn't a completed
    # pass but the team still wins the loose ball).
    detail = retention_detail(events, "corner")
    disagreements = detail[(detail["outcome"] == 0) & (detail["retained"] == True)]  # noqa: E712
    assert len(disagreements) > 0


def test_retention_rate_between_zero_and_one(events):
    rates = retention_rate(events, "throw_in")
    assert rates["retention_rate"].between(0, 1).all()
    assert (rates["retained"] <= rates["deliveries"]).all()
