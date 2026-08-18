from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import delivery_clip_windows, load_events
from wa_setpieces.core.filters import extract_corners

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_delivery_clip_windows_one_row_per_delivery(events):
    clips = delivery_clip_windows(events, "corner")
    assert len(clips) == len(extract_corners(events))
    assert {"clip_start_seconds", "clip_end_seconds", "event_seconds"}.issubset(clips.columns)


def test_clip_window_brackets_the_event(events):
    clips = delivery_clip_windows(events, "corner", pre_seconds=5, post_seconds=15)
    assert (clips["clip_start_seconds"] == clips["event_seconds"] - 5).all()
    assert (clips["clip_end_seconds"] == clips["event_seconds"] + 15).all()
    assert (clips["clip_start_seconds"] <= clips["event_seconds"]).all()
    assert (clips["clip_end_seconds"] >= clips["event_seconds"]).all()


def test_clip_start_clamps_at_zero_near_kickoff():
    row = dict(
        eventId=1, typeId=1, periodId=1, timeMin=0, timeSec=2, contestantId="A",
        playerId="p", playerName="P", outcome=1, x=99.5, y=99.5, q_6=True,
    )
    clips = delivery_clip_windows(pd.DataFrame([row]), "corner", pre_seconds=5, post_seconds=15)
    assert clips.iloc[0]["clip_start_seconds"] == 0.0
    assert clips.iloc[0]["clip_end_seconds"] == 17.0


def test_delivery_clip_windows_rejects_bad_type(events):
    with pytest.raises(ValueError):
        delivery_clip_windows(events, "not_a_real_type")


def test_delivery_clip_windows_rejects_negative_padding(events):
    with pytest.raises(ValueError):
        delivery_clip_windows(events, "corner", pre_seconds=-1)
    with pytest.raises(ValueError):
        delivery_clip_windows(events, "corner", post_seconds=-1)


def test_delivery_clip_windows_carries_match_id_when_present(events):
    from wa_setpieces import load_events_multi

    combined = load_events_multi([DATA, DATA], match_ids=["m1", "m2"])
    clips = delivery_clip_windows(combined, "corner")
    assert "matchId" in clips.columns
    assert set(clips["matchId"]) == {"m1", "m2"}
