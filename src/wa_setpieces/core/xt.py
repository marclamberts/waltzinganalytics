"""Expected Threat (xT) for corner and free-kick deliveries.

This implements the grid-based xT method (Karun Singh, 2018): the pitch is
split into a grid, and each zone gets a value equal to the probability of
scoring soon from that zone, computed by iterating between "shoot from
here" and "move the ball to a more dangerous zone" until the values
converge. The value added by an action is ``xT[end_zone] - xT[start_zone]``.

**The grid is fit from data you provide** -- there is no bundled,
pre-trained grid, because a trustworthy xT grid needs a large sample of
matches (thousands of actions per zone) to be statistically meaningful.
Fitting :meth:`XTModel.fit` on a single match (as in the bundled sample
data / docs examples) produces a grid that is illustrative of the
*mechanism* only; do not use it for real analysis. For production use, fit
on a full season or more, concatenating events across matches, and
persist the result with :meth:`XTModel.to_csv` / :meth:`XTModel.from_csv`
so you don't have to refit every time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import constants as c

DEFAULT_X_BINS = 16
DEFAULT_Y_BINS = 12


def _to_cell(x: np.ndarray, y: np.ndarray, x_bins: int, y_bins: int) -> tuple[np.ndarray, np.ndarray]:
    col = np.clip((x / 100 * x_bins).astype(int), 0, x_bins - 1)
    row = np.clip((y / 100 * y_bins).astype(int), 0, y_bins - 1)
    return row, col


@dataclass
class XTModel:
    """A fitted (or loaded) expected-threat grid.

    ``grid`` is a ``(y_bins, x_bins)`` array of xT values (0-1 scale).
    ``x_bins`` is the number of columns (pitch length direction) and
    ``y_bins`` the number of rows (pitch width direction).
    """

    grid: np.ndarray
    x_bins: int = DEFAULT_X_BINS
    y_bins: int = DEFAULT_Y_BINS
    shot_probability: np.ndarray | None = field(default=None, repr=False)
    move_probability: np.ndarray | None = field(default=None, repr=False)
    goal_probability: np.ndarray | None = field(default=None, repr=False)

    def cell(self, x: float, y: float) -> tuple[int, int]:
        row, col = _to_cell(np.array([x]), np.array([y]), self.x_bins, self.y_bins)
        return int(row[0]), int(col[0])

    def value(self, x: float, y: float) -> float:
        """xT value of a single pitch location."""
        if pd.isna(x) or pd.isna(y):
            return float("nan")
        row, col = self.cell(x, y)
        return float(self.grid[row, col])

    def action_value(self, start_x: float, start_y: float, end_x: float, end_y: float) -> float:
        """xT added by moving the ball from (start_x, start_y) to (end_x, end_y)."""
        return self.value(end_x, end_y) - self.value(start_x, start_y)

    def shot_value(self, x: float, y: float) -> float:
        """Scoring probability of a shot taken from (x, y): ``shot_probability * goal_probability``.

        Unlike :meth:`value` (the value of *having the ball* in a zone,
        counting both shooting and continuing to play), this is specifically
        "if a shot is taken from here, how often does it go in" -- the
        component :mod:`wa_setpieces.core.value` uses to score a set piece's
        resulting shot, separately from the delivery's own xT added.

        Only available on a model produced by :meth:`fit` (not one loaded
        via :meth:`from_csv`, which only persists the value grid).
        """
        if self.shot_probability is None or self.goal_probability is None:
            raise ValueError(
                "shot_value requires a model fit with XTModel.fit() -- "
                "shot/goal probability grids aren't persisted by to_csv/from_csv"
            )
        if pd.isna(x) or pd.isna(y):
            return float("nan")
        row, col = self.cell(x, y)
        return float(self.shot_probability[row, col] * self.goal_probability[row, col])

    def value_series(self, x: pd.Series, y: pd.Series) -> pd.Series:
        """Vectorized :meth:`value` over two aligned coordinate Series."""
        xn = pd.to_numeric(x, errors="coerce").to_numpy()
        yn = pd.to_numeric(y, errors="coerce").to_numpy()
        out = np.full(len(xn), np.nan)
        valid = ~(np.isnan(xn) | np.isnan(yn))
        row, col = _to_cell(xn[valid], yn[valid], self.x_bins, self.y_bins)
        out[valid] = self.grid[row, col]
        return pd.Series(out, index=x.index)

    def to_csv(self, path: str | Path) -> None:
        pd.DataFrame(self.grid).to_csv(path, index=False)

    @classmethod
    def from_csv(cls, path: str | Path) -> "XTModel":
        grid = pd.read_csv(path).to_numpy()
        return cls(grid=grid, y_bins=grid.shape[0], x_bins=grid.shape[1])

    @classmethod
    def fit(
        cls,
        events: pd.DataFrame,
        x_bins: int = DEFAULT_X_BINS,
        y_bins: int = DEFAULT_Y_BINS,
        n_iterations: int = 8,
    ) -> "XTModel":
        """Fit an xT grid from an events DataFrame (see :func:`load_events`).

        Uses all passes (``typeId==1``) and take-ons (``typeId==3``) as
        "moves", and all shot events (miss/post/saved/goal) as "shots", to
        build per-zone shot probability, scoring probability, and a
        zone-to-zone transition matrix. Values are then found by iterating
        the Bellman-style xT recurrence to convergence.

        Fit across as many matches as you can (concatenate their events
        DataFrames) -- a single match is nowhere near enough data for a
        reliable grid; see the module docstring.
        """
        moves = events[events["typeId"].isin((c.TYPE_PASS, c.TYPE_TAKE_ON))].copy()
        shots = events[events["typeId"].isin(c.SHOT_TYPE_IDS)].copy()

        n_cells = x_bins * y_bins
        move_count = np.zeros((y_bins, x_bins))
        shot_count = np.zeros((y_bins, x_bins))
        goal_count = np.zeros((y_bins, x_bins))
        transition_count = np.zeros((n_cells, n_cells))

        mx = pd.to_numeric(moves["x"], errors="coerce").to_numpy()
        my = pd.to_numeric(moves["y"], errors="coerce").to_numpy()
        outcome = pd.to_numeric(moves["outcome"], errors="coerce").fillna(0).to_numpy()
        end_x = pd.to_numeric(moves.get(f"q_{c.QUALIFIER_PASS_END_X}"), errors="coerce").to_numpy()
        end_y = pd.to_numeric(moves.get(f"q_{c.QUALIFIER_PASS_END_Y}"), errors="coerce").to_numpy()
        # Take-ons have no end-location qualifier; treat them as staying put
        # (they still count as a zone "action" for shot-probability purposes).
        end_x = np.where(np.isnan(end_x), mx, end_x)
        end_y = np.where(np.isnan(end_y), my, end_y)

        valid = ~(np.isnan(mx) | np.isnan(my))
        row, col = _to_cell(mx[valid], my[valid], x_bins, y_bins)
        erow, ecol = _to_cell(end_x[valid], end_y[valid], x_bins, y_bins)
        succ = outcome[valid] == 1

        np.add.at(move_count, (row, col), 1)
        from_idx = row * x_bins + col
        to_idx = erow * x_bins + ecol
        np.add.at(
            transition_count,
            (from_idx[succ], to_idx[succ]),
            1,
        )

        sx = pd.to_numeric(shots["x"], errors="coerce").to_numpy()
        sy = pd.to_numeric(shots["y"], errors="coerce").to_numpy()
        is_goal = (shots["typeId"] == c.TYPE_GOAL).to_numpy()
        svalid = ~(np.isnan(sx) | np.isnan(sy))
        srow, scol = _to_cell(sx[svalid], sy[svalid], x_bins, y_bins)
        np.add.at(shot_count, (srow, scol), 1)
        np.add.at(goal_count, (srow[is_goal[svalid]], scol[is_goal[svalid]]), 1)

        total_actions = move_count + shot_count
        with np.errstate(divide="ignore", invalid="ignore"):
            shot_probability = np.where(total_actions > 0, shot_count / total_actions, 0.0)
            move_probability = np.where(total_actions > 0, move_count / total_actions, 0.0)
            goal_probability = np.where(shot_count > 0, goal_count / shot_count, 0.0)

        transition_matrix = np.zeros_like(transition_count)
        row_totals = transition_count.sum(axis=1, keepdims=True)
        nonzero = row_totals[:, 0] > 0
        transition_matrix[nonzero] = transition_count[nonzero] / row_totals[nonzero]

        xt = np.zeros(n_cells)
        shot_value = (shot_probability * goal_probability).reshape(-1)
        move_prob_flat = move_probability.reshape(-1)
        for _ in range(n_iterations):
            move_value = transition_matrix @ xt
            xt = shot_value + move_prob_flat * move_value

        model = cls(
            grid=xt.reshape(y_bins, x_bins),
            x_bins=x_bins,
            y_bins=y_bins,
            shot_probability=shot_probability,
            move_probability=move_probability,
            goal_probability=goal_probability,
        )
        return model


def set_piece_delivery_xt(events: pd.DataFrame, set_piece_type: str, model: XTModel) -> pd.DataFrame:
    """xT added by each corner/free-kick delivery, using a fitted ``model``.

    Args:
        set_piece_type: ``"corner"`` or ``"free_kick"`` (a pass-based set
            piece with start/end coordinates).
        model: an :class:`XTModel`, typically from ``XTModel.fit(events)``.

    Returns:
        One row per delivery: eventId, contestantId, playerId, playerName,
        x, y, end_x, end_y, outcome, xt_start, xt_end, xt_added. ``xt_added``
        is NaN for unsuccessful deliveries (no reliable end location).
    """
    from .metrics import delivery_locations

    deliveries = delivery_locations(events, set_piece_type)
    xt_start = model.value_series(deliveries["x"], deliveries["y"])
    xt_end = model.value_series(deliveries["end_x"], deliveries["end_y"])
    deliveries = deliveries.copy()
    deliveries["xt_start"] = xt_start
    deliveries["xt_end"] = xt_end
    successful = pd.to_numeric(deliveries["outcome"], errors="coerce").fillna(0) == 1
    deliveries["xt_added"] = np.where(successful, xt_end - xt_start, np.nan)
    return deliveries


def set_piece_xt_summary(
    events: pd.DataFrame, set_piece_type: str, model: XTModel
) -> pd.DataFrame:
    """Per-team average/total xT added from corner or free-kick deliveries."""
    delivered = set_piece_delivery_xt(events, set_piece_type, model)
    out = (
        delivered.groupby("contestantId")
        .agg(
            deliveries=("eventId", "count"),
            successful_deliveries=("xt_added", lambda s: s.notna().sum()),
            total_xt_added=("xt_added", lambda s: s.fillna(0).sum()),
            avg_xt_added=("xt_added", "mean"),
        )
        .reset_index()
    )
    return out
