"""Team and player set-piece ratings: a single 0-100 "how good" score,
benchmarked against the peer group you pass in.

There is no universal 50 -- a rating is always relative to whoever else is
in the table with it. Score a team against its full league/season (via
:func:`~wa_setpieces.core.report.set_piece_report` over a whole
competition's events, not one match), or players against every player who
took/shot that set piece type over the same sample. A single-match sample
still runs, but a two-row z-score just tells you which of those two teams
had the better match, not how good either one actually is.

Each component metric is z-scored against the sample (``50 + z * 15``,
clipped to ``[0, 100]`` -- roughly SAT-style: 50 is the sample mean, +/-1
SD is +/-15 points), then combined by a weighted mean into ``rating``. A
zero-variance or single-row sample can't be benchmarked, so every row gets
50 rather than a division-by-zero error.

Team ratings build on :func:`~wa_setpieces.core.report.set_piece_report`'s
own columns (``success_rate``, ``avg_added_value``, ``retention_rate``).
Player ratings split into two separate, independently benchmarked halves
-- a **delivery score** (taker quality: :func:`~wa_setpieces.core.value.set_piece_added_value`,
grouped by who took the set piece) and a **finishing score** (shooter
quality: :meth:`~wa_setpieces.core.xt.XTModel.shot_value` on every shot
:func:`~wa_setpieces.core.chains.link_set_piece_shots` traces back to this
set piece type, grouped by who took the shot) -- since a player can be
good at one and never do the other; :func:`player_rating` then merges the
two so a pure taker or pure finisher is rated on the component they
actually have, not penalized for the one they don't.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .chains import link_set_piece_shots
from .value import set_piece_added_value
from .xt import XTModel

TEAM_RATING_WEIGHTS = {
    "success_rate": 1.0,
    "avg_added_value": 1.0,
    "retention_rate": 0.5,
}
PLAYER_DELIVERY_WEIGHTS = {
    "success_rate": 1.0,
    "avg_added_value": 1.0,
}
PLAYER_FINISHING_WEIGHTS = {
    "avg_shot_value": 1.0,
}


def _zscore_to_100(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if len(series) < 2 or not np.isfinite(std) or std == 0:
        return pd.Series(50.0, index=series.index)
    z = (series - series.mean()) / std
    return (50 + z * 15).clip(0, 100)


def _rate(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    available = [(metric, weight) for metric, weight in weights.items() if metric in df.columns]
    if not available:
        raise ValueError(
            f"none of the rating metrics {list(weights)} are present in the input "
            f"columns {list(df.columns)}"
        )
    out = df.copy()
    score_cols = []
    for metric, weight in available:
        score_col = f"{metric}_score"
        out[score_col] = _zscore_to_100(df[metric])
        score_cols.append((score_col, weight))
    total_weight = sum(weight for _, weight in score_cols)
    out["rating"] = (
        sum(out[col] * weight for col, weight in score_cols) / total_weight
    ).round(1)
    return out


def team_rating(report: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Add per-metric benchmark scores and a composite ``rating`` (0-100) to
    a :func:`~wa_setpieces.core.report.set_piece_report`-shaped table (one
    row per team, covering a full sample -- see the module docstring).

    ``weights`` defaults to :data:`TEAM_RATING_WEIGHTS`; only the metrics
    actually present in ``report`` are used -- pass a table from
    ``corner_report(events, model=xt_model)`` to include ``avg_added_value``,
    or without a model to rate on ``success_rate``/``retention_rate`` alone.
    """
    return _rate(report, weights or TEAM_RATING_WEIGHTS)


def player_delivery_rating(
    events: pd.DataFrame,
    set_piece_type: str,
    model: XTModel,
    weights: dict[str, float] | None = None,
    min_deliveries: int = 3,
) -> pd.DataFrame:
    """Per-player delivery-taker rating for one set-piece type: success rate
    and average added value (see :func:`~wa_setpieces.core.value.set_piece_added_value`),
    z-scored against every player in ``events`` with at least
    ``min_deliveries`` attempts (too few deliveries makes for a noisy
    z-score, not a real signal).
    """
    detail = set_piece_added_value(events, set_piece_type, model)
    agg = (
        detail.groupby(["playerId", "playerName", "contestantId"])
        .agg(
            deliveries=("eventId", "count"),
            success_rate=("outcome", lambda s: float((pd.to_numeric(s, errors="coerce") == 1).mean())),
            avg_added_value=("added_value", "mean"),
        )
        .reset_index()
    )
    agg = agg.loc[agg["deliveries"] >= min_deliveries].reset_index(drop=True)
    if agg.empty:
        return agg.assign(**{f"{m}_score": pd.Series(dtype=float) for m in (weights or PLAYER_DELIVERY_WEIGHTS)}, rating=pd.Series(dtype=float))
    return _rate(agg, weights or PLAYER_DELIVERY_WEIGHTS)


def player_finishing_rating(
    events: pd.DataFrame,
    set_piece_type: str,
    model: XTModel,
    min_shots: int = 1,
) -> pd.DataFrame:
    """Per-player finishing rating for shots traced back to one set-piece
    type via :func:`~wa_setpieces.core.chains.link_set_piece_shots`: goals
    and average :meth:`~wa_setpieces.core.xt.XTModel.shot_value`, z-scored
    against every player with at least ``min_shots`` such shots.
    """
    linked = link_set_piece_shots(events)
    shots = linked.loc[linked["set_piece_type"] == set_piece_type].copy()
    shots["shot_value"] = [
        model.shot_value(x, y) for x, y in zip(shots["x"], shots["y"])
    ]
    agg = (
        shots.groupby(["playerId", "playerName", "contestantId"])
        .agg(
            shots=("eventId", "count"),
            goals=("is_goal", "sum"),
            avg_shot_value=("shot_value", "mean"),
        )
        .reset_index()
    )
    agg = agg.loc[agg["shots"] >= min_shots].reset_index(drop=True)
    if agg.empty:
        return agg.assign(avg_shot_value_score=pd.Series(dtype=float), rating=pd.Series(dtype=float))
    return _rate(agg, PLAYER_FINISHING_WEIGHTS)


def player_rating(
    events: pd.DataFrame,
    set_piece_type: str,
    model: XTModel,
    min_deliveries: int = 3,
    min_shots: int = 1,
) -> pd.DataFrame:
    """Merge :func:`player_delivery_rating` and :func:`player_finishing_rating`
    into one table: ``delivery_score``, ``finishing_score`` (either may be
    NaN -- a player who only ever took corners has no finishing sample, and
    vice versa) and an overall ``rating``, the mean of whichever score(s)
    the player has. Sorted by ``rating`` descending.
    """
    delivery = player_delivery_rating(
        events, set_piece_type, model, min_deliveries=min_deliveries
    )[["playerId", "playerName", "contestantId", "deliveries", "rating"]].rename(
        columns={"rating": "delivery_score"}
    )
    finishing = player_finishing_rating(
        events, set_piece_type, model, min_shots=min_shots
    )[["playerId", "playerName", "contestantId", "shots", "rating"]].rename(
        columns={"rating": "finishing_score"}
    )
    merged = delivery.merge(
        finishing, on=["playerId", "playerName", "contestantId"], how="outer"
    )
    merged["rating"] = merged[["delivery_score", "finishing_score"]].mean(axis=1, skipna=True).round(1)
    return merged.sort_values("rating", ascending=False, na_position="last").reset_index(drop=True)
