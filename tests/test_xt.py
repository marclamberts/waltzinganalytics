from pathlib import Path

import numpy as np
import pytest

from wa_setpieces import load_events
from wa_setpieces.xt import XTModel, set_piece_delivery_xt, set_piece_xt_summary

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_fit_returns_grid_of_requested_shape(model):
    assert model.grid.shape == (6, 8)


def test_xt_values_are_bounded_and_non_negative(model):
    assert np.isfinite(model.grid).all()
    assert (model.grid >= 0).all()
    assert (model.grid <= 1).all()


def test_xt_increases_towards_goal(model):
    # Deep in the acting team's own half should be worth less than right in
    # front of the opponent's goal (using the confirmed F24 convention that
    # x=100 is always the acting team's attacking end).
    deep = model.value(5, 50)
    edge_of_box = model.value(85, 50)
    assert edge_of_box > deep


def test_action_value_end_minus_start(model):
    val = model.action_value(50, 50, 90, 50)
    assert val == pytest.approx(model.value(90, 50) - model.value(50, 50))


def test_value_series_matches_scalar_value(events, model):
    sample = events.dropna(subset=["x", "y"]).head(20)
    series = model.value_series(sample["x"], sample["y"])
    for (idx, row), v in zip(sample.iterrows(), series):
        assert v == pytest.approx(model.value(row["x"], row["y"]))


def test_to_csv_and_from_csv_round_trip(model, tmp_path):
    path = tmp_path / "grid.csv"
    model.to_csv(path)
    loaded = XTModel.from_csv(path)
    assert loaded.grid.shape == model.grid.shape
    assert np.allclose(loaded.grid, model.grid)


def test_set_piece_delivery_xt_has_expected_columns(events, model):
    out = set_piece_delivery_xt(events, "corner", model)
    assert {"xt_start", "xt_end", "xt_added"}.issubset(out.columns)
    assert len(out) == 9  # known corner count in the sample match


def test_set_piece_delivery_xt_added_nan_for_unsuccessful(events, model):
    out = set_piece_delivery_xt(events, "corner", model)
    unsuccessful = out[out["outcome"] == 0]
    assert unsuccessful["xt_added"].isna().all()


def test_set_piece_xt_summary_one_row_per_team(events, model):
    summary = set_piece_xt_summary(events, "free_kick", model)
    assert len(summary) == 2
    assert {"total_xt_added", "avg_xt_added"}.issubset(summary.columns)
