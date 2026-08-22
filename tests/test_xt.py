from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.core import constants as c
from wa_setpieces.core.xt import XTModel, set_piece_delivery_xt, set_piece_xt_summary

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_fit_returns_grid_of_requested_shape(model):
    assert model.grid.shape == (6, 8)


def test_xt_discounts_cells_with_low_pass_completion():
    # Regression test: the transition matrix must be normalized by total
    # move attempts (matching move_probability's own denominator), not by
    # the count of successful transitions alone -- otherwise a cell whose
    # passes rarely complete gets credited as if every attempt succeeded.
    # Two cells both send their (rare, for B) successful passes to the same
    # valuable cell right in front of goal; A completes 10/10, B only 1/10.
    def event(event_id, type_id, x, y, outcome=1, end_x=None, end_y=None):
        row = dict(
            eventId=event_id, typeId=type_id, periodId=1, timeMin=0, timeSec=event_id,
            contestantId="A", playerId="p", playerName="P", outcome=outcome, x=x, y=y,
        )
        if end_x is not None:
            row["q_140"] = end_x
        if end_y is not None:
            row["q_141"] = end_y
        return row

    rows = []
    i = 0
    for _ in range(10):
        i += 1
        rows.append(event(i, c.TYPE_PASS, 10, 50, outcome=1, end_x=90, end_y=50))
    i += 1
    rows.append(event(i, c.TYPE_PASS, 30, 50, outcome=1, end_x=90, end_y=50))
    for _ in range(9):
        i += 1
        rows.append(event(i, c.TYPE_PASS, 30, 50, outcome=0, end_x=35, end_y=52))
    for j in range(5):
        i += 1
        rows.append(event(i, c.TYPE_GOAL if j < 2 else c.TYPE_MISS, 90, 50))

    events = pd.DataFrame(rows)
    model = XTModel.fit(events, x_bins=10, y_bins=5, n_iterations=8)
    xt_a = model.value(10, 50)
    xt_b = model.value(30, 50)
    assert xt_a == pytest.approx(0.4)
    assert xt_b == pytest.approx(0.04)
    assert xt_a > xt_b * 5  # A's 100% completion must clearly outvalue B's 10%


def test_xt_values_are_bounded_and_non_negative(model):
    assert np.isfinite(model.grid).all()
    assert (model.grid >= 0).all()
    assert (model.grid <= 1).all()


def test_xt_increases_towards_goal(model):
    # Deep in the acting team's own half should be worth less than right in
    # front of the opponent's goal (using the confirmed convention that
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
