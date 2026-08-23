import pandas as pd
import pytest

from wa_setpieces.core.chains import link_set_piece_shots
from wa_setpieces.core.filters import extract_corners, tag_set_pieces
from wa_setpieces.providers.impect import load_impect_events

_BASE = {
    "match_id": 1001,
    "periodId": 1,
    "result": "SUCCESS",
    "bodyPart": None,
    "action": None,
    "duel.duelType": None,
    "setPiece.id": None,
    "setPiece.mainEvent": None,
    "start.adjCoordinates.x": None,
    "start.adjCoordinates.y": None,
    "end.adjCoordinates.x": None,
    "end.adjCoordinates.y": None,
    "player.id": None,
}


def _row(**overrides) -> dict:
    row = dict(_BASE)
    row.update(overrides)
    return row


CORNER_ID = 5001
SHOT_ID = 5002
RECEPTION_ID = 5003
GOAL_ID = 5004
PENALTY_ID = 5005


def _raw_frame() -> pd.DataFrame:
    rows = [
        _row(
            index=0, id=CORNER_ID, squadId=100, actionType="CORNER", action="CORNER",
            result="SUCCESS", **{
                "gameTime.gameTimeInSec": 600.0,
                "player.id": 10,
                "start.adjCoordinates.x": 52.5, "start.adjCoordinates.y": -34.0,
                "end.adjCoordinates.x": 45.0, "end.adjCoordinates.y": 10.0,
                "setPiece.id": 9001, "setPiece.mainEvent": True,
            },
        ),
        _row(
            index=1, id=RECEPTION_ID, squadId=100, actionType="RECEPTION", action="RECEPTION",
            result="SUCCESS", **{
                "gameTime.gameTimeInSec": 601.0,
                "player.id": 11,
                "start.adjCoordinates.x": 45.0, "start.adjCoordinates.y": 10.0,
                "setPiece.id": 9001, "setPiece.mainEvent": False,
            },
        ),
        _row(
            index=2, id=SHOT_ID, squadId=100, actionType="SHOT", action="MID_RANGE_SHOT",
            result="SUCCESS", **{
                "gameTime.gameTimeInSec": 603.0,
                "player.id": 11,
                "start.adjCoordinates.x": 46.0, "start.adjCoordinates.y": 12.0,
                "setPiece.id": 9001, "setPiece.mainEvent": False,
            },
        ),
        _row(
            index=3, id=GOAL_ID, squadId=100, actionType="GOAL", action="GOAL",
            result=None, **{"gameTime.gameTimeInSec": 603.0, "player.id": 11},
        ),
        _row(
            index=4, id=PENALTY_ID, squadId=200, actionType="SHOT", action="PENALTY_KICK",
            result="SUCCESS", periodId=2, **{
                "gameTime.gameTimeInSec": 10500.0,
                "player.id": 20,
                "start.adjCoordinates.x": 41.0, "start.adjCoordinates.y": 0.0,
            },
        ),
        _row(
            index=5, id=6006, squadId=None, actionType="NO_VIDEO", action="VIDEO_NOT_AVAILABLE",
            result=None, **{"gameTime.gameTimeInSec": 700.0},
        ),
    ]
    return pd.DataFrame(rows)


def test_load_impect_events_basic_shape():
    events = load_impect_events(_raw_frame())
    assert set(events["matchId"].unique()) == {"1001"}
    assert (events["playerName"].isna()).all()


def test_teamless_rows_are_dropped_not_left_with_null_eventid():
    events = load_impect_events(_raw_frame())
    assert events["eventId"].notna().all()
    assert len(events) == 5  # the NO_VIDEO row (no squadId) is dropped


def test_corner_is_tagged_and_end_coordinates_convert():
    events = load_impect_events(_raw_frame())
    corners = extract_corners(events)
    assert len(corners) == 1
    row = corners.iloc[0]
    # start.adjCoordinates (52.5, -34.0) is the corner-arc extreme in
    # IMPECT's centered 105x68 frame -> Opta's (100, 0).
    assert row["x"] == pytest.approx(100.0)
    assert row["y"] == pytest.approx(0.0)


def test_goal_row_is_not_double_counted_as_a_second_shot():
    events = load_impect_events(_raw_frame())
    from wa_setpieces.core import constants as c

    goal_row = events[events["id"] == GOAL_ID].iloc[0]
    assert goal_row["typeId"] not in c.SHOT_TYPE_IDS
    shot_row = events[events["id"] == SHOT_ID].iloc[0]
    assert shot_row["typeId"] == c.TYPE_GOAL  # result == SUCCESS


def test_penalty_is_flagged_via_qualifier():
    from wa_setpieces.core import constants as c

    events = load_impect_events(_raw_frame())
    penalty_row = events[events["id"] == PENALTY_ID].iloc[0]
    assert penalty_row[f"q_{c.QUALIFIER_PENALTY}"] is True


def test_set_piece_id_links_shot_back_to_the_corner():
    events = load_impect_events(_raw_frame())
    shots = link_set_piece_shots(events)
    # Two set pieces in the fixture: the corner (linked to its shot via
    # setPiece.id) and the standalone penalty (a set piece in its own
    # right -- no separate delivery to link back to).
    linked = shots[shots["set_piece_type"].notna()]
    assert set(linked["set_piece_type"]) == {"corner", "penalty"}
    corner_shot = linked[linked["set_piece_type"] == "corner"].iloc[0]
    assert bool(corner_shot["is_goal"]) is True
    assert corner_shot["set_piece_event_id"] == 1  # the corner's own eventId


def test_tag_set_pieces_finds_the_corner():
    events = load_impect_events(_raw_frame())
    tagged = tag_set_pieces(events)
    assert (tagged["set_piece_type"] == "corner").sum() == 1


def test_second_period_time_offset_is_removed():
    events = load_impect_events(_raw_frame())
    penalty_row = events[events["id"] == PENALTY_ID].iloc[0]
    # periodId 2's gameTimeInSec (10500.0) minus the 10000s period offset is
    # 500s elapsed in the second half; cumulative from kickoff assuming
    # 45-minute halves is 45*60 + 500 = 3200s -> 53 min 20 sec.
    assert penalty_row["timeMin"] == 53
    assert penalty_row["timeSec"] == 20


def test_load_impect_events_accepts_a_path(tmp_path):
    csv_path = tmp_path / "impect.csv"
    _raw_frame().to_csv(csv_path, index=False)
    events = load_impect_events(csv_path)
    assert not events.empty


def test_load_impect_events_accepts_a_json_path(tmp_path):
    # Same raw record shape as the CSV export, just JSON-encoded (e.g.
    # ``raw_df.to_json(orient="records")``) -- provider is what decides
    # how a file is parsed, not its extension.
    json_path = tmp_path / "impect.json"
    _raw_frame().to_json(json_path, orient="records")
    csv_events = load_impect_events(_raw_frame())
    json_events = load_impect_events(json_path)
    assert not json_events.empty
    assert list(json_events["id"]) == list(csv_events["id"])
    assert list(json_events["typeId"]) == list(csv_events["typeId"])


def test_load_impect_events_empty_input_returns_empty_frame():
    events = load_impect_events(pd.DataFrame())
    assert events.empty


def test_load_impect_events_without_setpiece_columns():
    # Regression test: a stripped/partial IMPECT export missing the
    # optional setPiece.id/setPiece.mainEvent columns entirely used to
    # raise KeyError on direct column indexing rather than degrading to
    # "no assist-chain linking available."
    row = {
        "match_id": 1, "index": 0, "id": 1, "squadId": 100, "periodId": 1,
        "actionType": "CORNER", "action": "CORNER", "result": "SUCCESS",
        "gameTime.gameTimeInSec": 600.0,
    }
    events = load_impect_events(pd.DataFrame([row]))
    assert len(events) == 1
