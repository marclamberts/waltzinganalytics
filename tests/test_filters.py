from pathlib import Path

import pytest

from opta_setpieces import (
    extract_all,
    extract_corners,
    extract_free_kicks,
    extract_goal_kicks,
    extract_kick_offs,
    extract_penalties,
    extract_throw_ins,
    load_events,
    tag_set_pieces,
)
from opta_setpieces import constants as c

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_extract_counts_match_known_totals(events):
    # Cross-checked against the qualifierId distribution in the raw feed.
    assert len(extract_corners(events)) == 9
    assert len(extract_free_kicks(events)) == 25
    assert len(extract_throw_ins(events)) == 50
    assert len(extract_goal_kicks(events)) == 12
    assert len(extract_kick_offs(events)) == 4
    assert len(extract_penalties(events)) == 0  # no penalty in this match


def test_extract_all_matches_individual_extractors(events):
    all_sp = extract_all(events)
    assert set(all_sp) == set(c.SET_PIECE_TYPES)
    assert len(all_sp["corner"]) == len(extract_corners(events))
    assert len(all_sp["throw_in"]) == len(extract_throw_ins(events))


def test_corners_are_all_passes_from_corner_arc(events):
    corners = extract_corners(events)
    assert (corners["typeId"] == c.TYPE_PASS).all()
    # Corner arcs sit at the pitch corners: x near 0/100, y near 0/100.
    near_corner_x = (corners["x"] < 2) | (corners["x"] > 98)
    assert near_corner_x.all()


def test_throw_ins_originate_on_touchline(events):
    throw_ins = extract_throw_ins(events)
    on_touchline = (throw_ins["y"] < 2) | (throw_ins["y"] > 98)
    assert on_touchline.all()


def test_kick_offs_originate_at_centre_spot(events):
    kick_offs = extract_kick_offs(events)
    assert ((kick_offs["x"] - 50).abs() < 5).all()
    assert ((kick_offs["y"] - 50).abs() < 5).all()


def test_free_kicks_and_corners_are_mutually_exclusive(events):
    fk_ids = set(extract_free_kicks(events)["eventId"])
    corner_ids = set(extract_corners(events)["eventId"])
    assert fk_ids.isdisjoint(corner_ids)


def test_tag_set_pieces_adds_column_and_covers_all_extracted_events(events):
    tagged = tag_set_pieces(events)
    assert "set_piece_type" in tagged.columns
    total_tagged = tagged["set_piece_type"].notna().sum()
    total_extracted = sum(len(df) for df in extract_all(events).values())
    assert total_tagged == total_extracted
