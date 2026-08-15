from pathlib import Path

import pytest

from wa_setpieces import (
    EventSchemaError, SeasonDataset, defensive_rating, defensive_set_piece_summary,
    event_capabilities, first_contact_detail, load_events, validate_events,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_validate_and_capabilities(events):
    assert validate_events(events) is events
    assert event_capabilities(events).end_locations


def test_validation_explains_missing_columns(events):
    with pytest.raises(EventSchemaError, match="typeId"):
        validate_events(events.drop(columns="typeId"))


def test_season_summary_is_match_safe():
    season = SeasonDataset.from_sources([DATA, DATA], match_ids=["one", "two"])
    summary = season.summary()
    single = SeasonDataset.from_sources([DATA], match_ids=["one"]).summary()
    assert summary["matches"].eq(2).all()
    assert summary["attempts"].sum() == 2 * single["attempts"].sum()


def test_season_rolling_summary():
    season = SeasonDataset.from_sources([DATA, DATA], match_ids=["one", "two"])
    assert "rolling_success_rate" in season.rolling_summary(window=2)


def test_defensive_summary_and_rating(events):
    summary = defensive_set_piece_summary(events)
    assert {"shots_conceded", "goals_conceded", "shots_conceded_per_100"}.issubset(summary)
    assert defensive_rating(summary)["rating"].between(0, 100).all()


def test_first_contact_is_explicitly_heuristic(events):
    detail = first_contact_detail(events, "corner")
    assert len(detail) == 9
    assert set(detail["confidence"]) == {"event_sequence"}
