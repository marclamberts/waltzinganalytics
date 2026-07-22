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
    assert row["q_22"] is True  # headed
    assert row["q_103"] == "30.0"  # statsbomb_xg * 100


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


def test_load_statsbomb_events_accepts_a_json_file(tmp_path):
    import json

    path = tmp_path / "events.json"
    path.write_text(json.dumps(RAW_EVENTS))
    events = load_statsbomb_events(path)
    assert len(events) == 3


def test_load_statsbomb_events_empty_list_returns_empty_frame():
    events = load_statsbomb_events([])
    assert events.empty
