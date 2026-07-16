from pathlib import Path

import pytest

from wa_setpieces import load_events, load_events_multi

DATA = Path(__file__).parent / "data" / "sample_match.json"


def test_load_events_returns_match():
    match = load_events(DATA)
    assert match.match_details["matchStatus"] == "Played"
    assert not match.events.empty


def test_core_columns_present():
    match = load_events(DATA)
    for col in ("id", "eventId", "typeId", "periodId", "timeMin", "x", "y"):
        assert col in match.events.columns


def test_events_sorted_by_time():
    match = load_events(DATA)
    ev = match.events
    ordering = list(zip(ev["periodId"], ev["timeMin"], ev["timeSec"]))
    assert ordering == sorted(ordering)


def test_load_events_accepts_dict():
    import json

    with DATA.open() as fh:
        raw = json.load(fh)
    match = load_events(raw)
    assert not match.events.empty


def test_load_events_multi_tags_matchid_and_stacks_rows():
    single = load_events(DATA).events
    combined = load_events_multi([DATA, DATA], match_ids=["m1", "m2"])
    assert list(combined["matchId"].unique()) == ["m1", "m2"]
    assert len(combined) == 2 * len(single)
    assert (combined[combined["matchId"] == "m1"]["eventId"].values == single["eventId"].values).all()


def test_load_events_multi_default_match_ids_use_filename_stem():
    combined = load_events_multi([DATA])
    assert combined["matchId"].iloc[0] == DATA.stem


def test_load_events_multi_rejects_mismatched_match_ids_length():
    with pytest.raises(ValueError):
        load_events_multi([DATA, DATA], match_ids=["only_one"])


def test_load_events_multi_empty_sources():
    combined = load_events_multi([])
    assert combined.empty
    assert "matchId" in combined.columns
