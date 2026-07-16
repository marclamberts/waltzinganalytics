from pathlib import Path

from opta_setpieces import load_events

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
