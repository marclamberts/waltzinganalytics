import shutil
from pathlib import Path

import pytest

from wa_setpieces import load_events, load_events_multi, load_matches

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


def test_load_events_multi_rejects_duplicate_default_match_ids():
    # Regression test: two sources with the same file stem (e.g. the same
    # filename from two different directories, or the same file passed
    # twice by mistake) used to silently derive the same matchId for both,
    # merging two distinct matches under one ID -- defeating every
    # matchId-based safety this module and SeasonDataset build on top of.
    with pytest.raises(ValueError, match="duplicate matchId"):
        load_events_multi([DATA, DATA])


def test_load_events_multi_rejects_duplicate_explicit_match_ids():
    with pytest.raises(ValueError, match="duplicate matchId"):
        load_events_multi([DATA, DATA], match_ids=["m1", "m1"])


def test_load_matches_single_opta_file():
    events = load_matches(DATA, provider="opta")
    assert not events.empty
    assert set(events["matchId"].unique()) == {"sample_match"}


def test_load_matches_provider_is_case_insensitive():
    events = load_matches(DATA, provider="Opta")
    assert not events.empty


def test_load_matches_rejects_unknown_provider():
    with pytest.raises(ValueError, match="provider must be one of"):
        load_matches(DATA, provider="wyscout")


def test_load_matches_rejects_unknown_type():
    with pytest.raises(ValueError, match="type must be one of"):
        load_matches(DATA, provider="opta", type="tournament")


def test_load_matches_type_match_rejects_a_directory(tmp_path):
    with pytest.raises(ValueError, match="type='match' expects a single file"):
        load_matches(tmp_path, provider="opta", type="match")


def test_load_matches_type_season_rejects_a_single_file():
    with pytest.raises(ValueError, match="type='season' expects a directory"):
        load_matches(DATA, provider="opta", type="season")


def test_load_matches_folder_combines_every_file(tmp_path):
    # Two copies of the same match under different filenames -- load_matches
    # doesn't know (or care) they're the "same" match; it just derives one
    # matchId per file, same convention as load_events_multi.
    shutil.copy(DATA, tmp_path / "match_a.json")
    shutil.copy(DATA, tmp_path / "match_b.json")
    events = load_matches(tmp_path, provider="opta", type="season")
    assert set(events["matchId"].unique()) == {"match_a", "match_b"}
    assert len(events) == 2 * len(load_events(DATA).events)


def test_load_matches_folder_with_no_matching_files_raises(tmp_path):
    (tmp_path / "not_a_match.txt").write_text("nothing here")
    with pytest.raises(FileNotFoundError):
        load_matches(tmp_path, provider="opta", type="season")


def test_load_matches_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        load_matches("tests/data/does_not_exist.json", provider="opta", type="match")


def test_load_matches_skips_non_event_json_in_a_statsbomb_folder(tmp_path):
    # Regression test: a folder of StatsBomb exports commonly has a
    # matches.json/competitions.json sidecar file alongside the per-match
    # event files -- both are also *.json, so the folder scan picks it up
    # too. Confirmed against a real 241-match export where this silently
    # produced 242 rows of empty/typeId-0 garbage before providers.statsbomb
    # validated its input shape.
    import json

    sb_event = [{
        "id": "11111111-0000-0000-0000-000000000001", "index": 1, "period": 1,
        "minute": 10, "second": 0, "timestamp": "00:10:00.000",
        "type": {"id": 30, "name": "Pass"}, "team": {"id": 100, "name": "Home FC"},
        "player": {"id": 10, "name": "Taker"}, "location": [50.0, 40.0],
        "pass": {"end_location": [60.0, 40.0]},
    }]
    (tmp_path / "match_a.json").write_text(json.dumps(sb_event), encoding="utf-8")
    (tmp_path / "matches.json").write_text('[{"match_id": 1, "match_date": "2024-01-01"}]', encoding="utf-8")

    with pytest.warns(UserWarning, match="skipped"):
        events = load_matches(tmp_path, provider="statsbomb", type="season")

    assert set(events["matchId"].unique()) == {"match_a"}
    assert events["eventId"].notna().all()


def test_load_matches_raises_when_every_file_fails(tmp_path):
    (tmp_path / "matches.json").write_text('[{"match_id": 1}]', encoding="utf-8")
    with pytest.raises(ValueError, match="None of the"):
        load_matches(tmp_path, provider="statsbomb", type="season")
