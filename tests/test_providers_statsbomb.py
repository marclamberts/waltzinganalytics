import pandas as pd
import pytest

from wa_setpieces.core.chains import link_set_piece_shots
from wa_setpieces.core.filters import extract_corners, tag_set_pieces
from wa_setpieces.providers.statsbomb import load_statsbomb_events

CORNER_PASS_ID = "11111111-0000-0000-0000-000000000001"
SHOT_ID = "22222222-0000-0000-0000-000000000002"
PRESSURE_ID = "33333333-0000-0000-0000-000000000003"

RAW_EVENTS = [
    {
        "id": CORNER_PASS_ID,
        "index": 1,
        "period": 1,
        "minute": 10,
        "second": 0,
        "timestamp": "00:10:00.000",
        "type": {"id": 30, "name": "Pass"},
        "team": {"id": 100, "name": "Home FC"},
        "player": {"id": 10, "name": "Taker"},
        "location": [102.0, 0.5],
        "pass": {
            "type": {"id": 61, "name": "Corner"},
            "end_location": [110.0, 40.0],
            "technique": {"id": 1, "name": "Inswinging"},
        },
    },
    {
        "id": PRESSURE_ID,
        "index": 2,
        "period": 1,
        "minute": 10,
        "second": 1,
        "timestamp": "00:10:01.000",
        "type": {"id": 17, "name": "Pressure"},
        "team": {"id": 200, "name": "Away FC"},
        "player": {"id": 20, "name": "Presser"},
        "location": [108.0, 38.0],
    },
    {
        "id": SHOT_ID,
        "index": 3,
        "period": 1,
        "minute": 10,
        "second": 2,
        "timestamp": "00:10:02.000",
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": 100, "name": "Home FC"},
        "player": {"id": 11, "name": "Scorer"},
        "location": [115.0, 42.0],
        "shot": {
            "outcome": {"id": 97, "name": "Goal"},
            "body_part": {"id": 37, "name": "Head"},
            "statsbomb_xg": 0.3,
            "key_pass_id": CORNER_PASS_ID,
        },
    },
]


@pytest.fixture(scope="module")
def events():
    return load_statsbomb_events(RAW_EVENTS)


def test_returns_one_row_per_event_sorted_by_time(events):
    assert len(events) == 3
    assert list(events["eventId"]) == [1, 2, 3]


def test_pass_maps_to_type_pass_with_corner_qualifier(events):
    row = events.iloc[0]
    assert row["typeId"] == 1
    assert row["q_6"] is True  # QUALIFIER_CORNER_TAKEN
    assert row["outcome"] == 1  # no pass.outcome key -> complete


def test_pass_technique_uses_inswinger_qualifier_not_left_footed(events):
    # Regression test: this used to tag "Inswinging" with q_72, which in
    # this package's Opta-derived schema means "Left Footed" (see
    # core.constants.QUALIFIER_LEFT_FOOTED / the convert.corners fix for
    # the same underlying qualifierId mix-up). That made StatsBomb-sourced
    # data disagree with Opta-native data on what q_72 means, and silently
    # broke core.routines' delivery_technique detection for StatsBomb
    # corners. The real in-swinger qualifier is 223.
    from wa_setpieces.core.routines import restart_routines

    row = events.iloc[0]
    assert row.get("q_223") is True
    assert "q_72" not in events.columns or pd.isna(row.get("q_72"))

    detail = restart_routines(events, "corner")
    assert detail.iloc[0]["delivery_technique"] == "inswinger"


def test_pass_end_location_rescaled_to_opta_0_100(events):
    row = events.iloc[0]
    assert row["q_140"] == pytest.approx(str(round(110.0 * 100 / 120, 2)))
    assert row["q_141"] == pytest.approx(str(round(40.0 * 100 / 80, 2)))


def test_start_location_rescaled_to_opta_0_100(events):
    row = events.iloc[0]
    assert row["x"] == pytest.approx(102.0 * 100 / 120, abs=0.01)
    assert row["y"] == pytest.approx(0.5 * 100 / 80, abs=0.01)


def test_unmapped_event_type_gets_generic_type_other(events):
    row = events.iloc[1]
    assert row["typeId"] == 0
    assert row["contestantId"] == 200


def test_shot_maps_outcome_to_type_goal_and_flags_header(events):
    row = events.iloc[2]
    assert row["typeId"] == 16  # TYPE_GOAL
    assert row["q_15"] is True  # headed -- QUALIFIER_HEADED


def test_shot_statsbomb_xg_is_not_written_as_a_qualifier():
    # Regression test: statsbomb_xg used to be written into q_103, which
    # collides with core.placement.QUALIFIER_GOAL_MOUTH_Z (103) -- the feed has
    # no xG qualifier for it to correctly map onto, and the collision
    # silently corrupted ml.shot_value's goal_h_norm placement feature for
    # every StatsBomb-sourced shot with a nonzero xG.
    from wa_setpieces.core.placement import QUALIFIER_GOAL_MOUTH_Z

    events = load_statsbomb_events(RAW_EVENTS)
    row = events.iloc[2]
    assert f"q_{QUALIFIER_GOAL_MOUTH_Z}" not in events.columns or pd.isna(row.get(f"q_{QUALIFIER_GOAL_MOUTH_Z}"))


def test_shot_links_back_to_corner_via_related_event_qualifier(events):
    row = events.iloc[2]
    assert row["q_55"] == "1"  # eventId of the corner pass


def test_extract_corners_finds_the_converted_corner(events):
    corners = extract_corners(events)
    assert len(corners) == 1
    assert corners.iloc[0]["playerName"] == "Taker"


def test_tag_set_pieces_labels_the_corner(events):
    tagged = tag_set_pieces(events)
    assert tagged.loc[tagged["eventId"] == 1, "set_piece_type"].iloc[0] == "corner"


def test_chains_links_the_goal_back_to_the_corner(events):
    linked = link_set_piece_shots(events)
    goal_row = linked[linked["is_goal"]].iloc[0]
    assert goal_row["set_piece_type"] == "corner"
    assert goal_row["set_piece_event_id"] == 1
    assert goal_row["playerName"] == "Scorer"


def test_pass_outswinging_technique_uses_outswinger_qualifier():
    raw = [{
        "id": "a", "index": 1, "period": 1, "minute": 0, "second": 0,
        "timestamp": "00:00:00.000", "type": {"id": 30, "name": "Pass"},
        "team": {"id": 100, "name": "Home FC"}, "player": {"id": 10, "name": "Taker"},
        "location": [102.0, 0.5],
        "pass": {
            "type": {"id": 61, "name": "Corner"},
            "end_location": [110.0, 40.0],
            "technique": {"id": 2, "name": "Outswinging"},
        },
    }]
    row = load_statsbomb_events(raw).iloc[0]
    assert row.get("q_224") == True  # noqa: E712  # QUALIFIER_OUTSWINGER


def test_pass_headed_body_part_uses_head_pass_qualifier():
    raw = [{
        "id": "a", "index": 1, "period": 1, "minute": 0, "second": 0,
        "timestamp": "00:00:00.000", "type": {"id": 30, "name": "Pass"},
        "team": {"id": 100, "name": "Home FC"}, "player": {"id": 10, "name": "Taker"},
        "location": [50.0, 40.0],
        "pass": {"body_part": {"id": 37, "name": "Head"}},
    }]
    row = load_statsbomb_events(raw).iloc[0]
    assert row.get("q_3") == True  # noqa: E712  # QUALIFIER_HEAD_PASS


def test_shot_blocked_outcome_uses_blocked_qualifier():
    raw = [{
        "id": "a", "index": 1, "period": 1, "minute": 0, "second": 0,
        "timestamp": "00:00:00.000", "type": {"id": 16, "name": "Shot"},
        "team": {"id": 100, "name": "Home FC"}, "player": {"id": 10, "name": "Scorer"},
        "location": [110.0, 40.0],
        "shot": {"outcome": {"id": 96, "name": "Blocked"}},
    }]
    events = load_statsbomb_events(raw)
    row = events.iloc[0]
    assert row["typeId"] == 15  # TYPE_ATTEMPT_SAVED
    assert row.get("q_82") == True  # noqa: E712


def test_shot_penalty_type_uses_penalty_qualifier():
    raw = [{
        "id": "a", "index": 1, "period": 1, "minute": 0, "second": 0,
        "timestamp": "00:00:00.000", "type": {"id": 16, "name": "Shot"},
        "team": {"id": 100, "name": "Home FC"}, "player": {"id": 10, "name": "Taker"},
        "location": [111.0, 40.0],
        "shot": {"outcome": {"id": 97, "name": "Goal"}, "type": {"id": 88, "name": "Penalty"}},
    }]
    row = load_statsbomb_events(raw).iloc[0]
    assert row.get("q_9") == True  # noqa: E712  # QUALIFIER_PENALTY


def test_load_statsbomb_events_accepts_a_json_file(tmp_path):
    import json

    path = tmp_path / "events.json"
    path.write_text(json.dumps(RAW_EVENTS))
    events = load_statsbomb_events(path)
    assert len(events) == 3


def test_load_statsbomb_events_accepts_a_csv_round_trip(tmp_path):
    # A .csv is treated as already-converted (e.g. a previous run's
    # events.to_csv(...)) rather than a native StatsBomb export -- provider
    # is what decides how a file is parsed, not its extension.
    original = load_statsbomb_events(RAW_EVENTS)
    csv_path = tmp_path / "events.csv"
    original.to_csv(csv_path, index=False)
    reloaded = load_statsbomb_events(csv_path)
    assert list(reloaded["eventId"]) == list(original["eventId"])
    assert list(reloaded["typeId"]) == list(original["typeId"])


def test_load_statsbomb_events_empty_list_returns_empty_frame():
    events = load_statsbomb_events([])
    assert events.empty


def test_load_statsbomb_events_empty_list_still_has_core_columns():
    # Regression test: an empty rows list used to produce a columnless
    # DataFrame (pd.DataFrame([]) has no columns at all), which failed
    # schema.validate_events for the wrong reason -- "missing required
    # columns" instead of correctly handling a legitimately empty export.
    # Same bug as core.loader.load_events had for a zero-event match.
    from wa_setpieces.core.schema import validate_events

    events = load_statsbomb_events([])
    for col in ("id", "eventId", "typeId", "periodId", "timeMin", "timeSec", "contestantId", "outcome", "x", "y"):
        assert col in events.columns
    validate_events(events)


def test_load_statsbomb_events_rejects_a_non_event_list():
    # Regression test: a matches.json/competitions.json record (also a
    # JSON list, but of match metadata, not events) used to silently
    # produce a row of empty/typeId-0 garbage per record instead of a
    # clear error -- caught against a real StatsBomb export where this
    # corrupted a 241-match season-combined frame with no error at all
    # until validate_events rejected it several steps downstream.
    matches_json_shaped = [{"match_id": 1, "match_date": "2024-01-01", "home_team": {}}]
    with pytest.raises(ValueError, match="doesn't look like a StatsBomb events export"):
        load_statsbomb_events(matches_json_shaped)


def test_load_statsbomb_events_rejects_a_non_list_top_level(tmp_path):
    # A bare dict source is coerced via list(source) before it would ever
    # reach the shape check, so this specifically exercises the file-path
    # branch, where json.load can genuinely return a non-list (e.g. an
    # Opta-shaped {"matchDetails": ..., "event": [...]} file passed with
    # the wrong provider).
    import json

    path = tmp_path / "opta_shaped.json"
    path.write_text(json.dumps({"matchDetails": {}, "event": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="expected a StatsBomb events export"):
        load_statsbomb_events(path)
