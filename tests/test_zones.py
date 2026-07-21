from pathlib import Path

import pytest

from wa_setpieces import load_events
from wa_setpieces.core.zones import add_channels, add_thirds, add_zone_grid, zone_counts, zone_id

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_add_thirds_labels_known_points():
    assert zone_id(50, 50) is not None


def test_add_thirds_classifies_correctly(events):
    tagged = add_thirds(events)
    defensive = tagged[tagged["third"] == "defensive_third"]
    attacking = tagged[tagged["third"] == "attacking_third"]
    assert (defensive["x"] < 100 / 3).all()
    assert (attacking["x"] >= 200 / 3).all()


def test_add_channels_5_way(events):
    tagged = add_channels(events, n=5)
    assert set(tagged["channel"].dropna().unique()) <= {
        "left_wide",
        "left_half_space",
        "central",
        "right_half_space",
        "right_wide",
    }


def test_add_channels_3_way(events):
    tagged = add_channels(events, n=3)
    assert set(tagged["channel"].dropna().unique()) <= {"left", "central", "right"}


def test_add_channels_rejects_bad_n(events):
    with pytest.raises(ValueError):
        add_channels(events, n=4)


def test_zone_id_corners_of_grid():
    assert zone_id(0, 0, x_bins=6, y_bins=3) == "R0C0"
    assert zone_id(99.9, 99.9, x_bins=6, y_bins=3) == "R2C5"
    assert zone_id(100, 100, x_bins=6, y_bins=3) == "R2C5"  # clamp upper edge


def test_zone_id_handles_nan():
    import math

    assert zone_id(math.nan, 50) is None


def test_add_zone_grid_default_18_zones(events):
    tagged = add_zone_grid(events)
    zones = tagged["zone"].dropna().unique()
    assert len(zones) <= 18


def test_zone_counts_groups_by_team(events):
    counts = zone_counts(events, group_cols=["contestantId"])
    assert {"contestantId", "zone", "count"}.issubset(counts.columns)
    assert counts["count"].sum() == len(events.dropna(subset=["x", "y"]))
