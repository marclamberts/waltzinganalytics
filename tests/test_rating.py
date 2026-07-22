from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.core.rating import (
    _zscore_to_100,
    player_delivery_rating,
    player_finishing_rating,
    player_rating,
    team_rating,
)
from wa_setpieces.core.report import corner_report
from wa_setpieces.core.xt import XTModel

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_zscore_to_100_centers_on_fifty():
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    scored = _zscore_to_100(series)
    assert scored.mean() == pytest.approx(50.0)
    assert scored.idxmax() == series.idxmax()


def test_zscore_to_100_returns_fifty_for_zero_variance():
    series = pd.Series([3.0, 3.0, 3.0])
    assert (_zscore_to_100(series) == 50.0).all()


def test_zscore_to_100_returns_fifty_for_single_row():
    series = pd.Series([7.0])
    assert (_zscore_to_100(series) == 50.0).all()


def test_zscore_to_100_is_clipped_to_0_100():
    series = pd.Series([0.0, 0.0, 0.0, 0.0, 1000.0])
    scored = _zscore_to_100(series)
    assert scored.between(0, 100).all()


def test_team_rating_adds_component_and_composite_columns(events, model):
    report = corner_report(events, model=model)
    rated = team_rating(report)
    assert "rating" in rated.columns
    assert "success_rate_score" in rated.columns
    assert "avg_added_value_score" in rated.columns
    assert rated["rating"].between(0, 100).all()


def test_team_rating_uses_only_available_metrics_without_model(events):
    report = corner_report(events)  # no model -> no avg_added_value column
    rated = team_rating(report)
    assert "avg_added_value_score" not in rated.columns
    assert "success_rate_score" in rated.columns


def test_team_rating_raises_when_no_metrics_present():
    with pytest.raises(ValueError):
        team_rating(pd.DataFrame({"contestantId": ["a", "b"]}))


def test_player_delivery_rating_filters_by_min_deliveries(events, model):
    rated = player_delivery_rating(events, "corner", model, min_deliveries=1)
    assert (rated["deliveries"] >= 1).all()
    strict = player_delivery_rating(events, "corner", model, min_deliveries=1000)
    assert strict.empty


def test_player_finishing_rating_filters_by_min_shots(events, model):
    rated = player_finishing_rating(events, "corner", model, min_shots=1)
    assert (rated["shots"] >= 1).all()
    strict = player_finishing_rating(events, "corner", model, min_shots=1000)
    assert strict.empty


def test_player_rating_merges_delivery_and_finishing(events, model):
    rated = player_rating(events, "corner", model, min_deliveries=1, min_shots=1)
    assert {"delivery_score", "finishing_score", "rating"}.issubset(rated.columns)
    # rating is the mean of whichever score(s) a player has, never NaN when
    # at least one of the two components is present.
    has_either = rated["delivery_score"].notna() | rated["finishing_score"].notna()
    assert rated.loc[has_either, "rating"].notna().all()
    assert (rated["rating"].dropna() == rated["rating"].dropna().sort_values(ascending=False)).all()
