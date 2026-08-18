"""Penalty-specific enrichment: placement zone and per-taker conversion.

Penalties are shots, not passes -- unlike every other set piece this
package covers, they're detected on shot events (see
:func:`~wa_setpieces.core.filters.extract_penalties`), and
:mod:`wa_setpieces.core.routines`' ``routine_type`` for them is just the
shot result (scored/saved/post/missed). This module adds *where in the
goal* each penalty was placed, reusing
:func:`wa_setpieces.core.placement.goal_placement` -- the same
goal-mouth-qualifier geometry :mod:`wa_setpieces.ml.shot_value`'s shot-value
models were built on. Pure geometry, no optional dependency needed.
"""

from __future__ import annotations

import pandas as pd

from . import constants as c
from .filters import extract_penalties
from .placement import goal_placement

_RESULT = {
    c.TYPE_GOAL: "scored",
    c.TYPE_ATTEMPT_SAVED: "saved",
    c.TYPE_POST: "post",
    c.TYPE_MISS: "missed",
}

_DETAIL_COLUMNS = [
    "eventId", "contestantId", "playerId", "playerName", "result",
    "goal_y_norm", "goal_h_norm", "corner_zone", "placement_score",
]


def penalty_placement_detail(events: pd.DataFrame) -> pd.DataFrame:
    """One row per penalty: taker, result, and placement zone in the goal.

    Placement fields (``goal_y_norm``, ``goal_h_norm``, ``corner_zone``,
    ``placement_score``) come from
    :func:`~wa_setpieces.core.placement.goal_placement` -- see that
    module's docstring for what's confirmed vs guessed about qualifiers
    102/103. ``NaN``/``-1`` when those qualifiers aren't present in the feed.
    """
    penalties = extract_penalties(events)
    if penalties.empty:
        return pd.DataFrame(columns=_DETAIL_COLUMNS)

    rows = []
    for _, row in penalties.iterrows():
        placement = goal_placement(row)
        rows.append({
            "eventId": row["eventId"],
            "contestantId": row["contestantId"],
            "playerId": row.get("playerId"),
            "playerName": row.get("playerName"),
            "result": _RESULT.get(row["typeId"], "missed"),
            "goal_y_norm": placement["goal_y_norm"],
            "goal_h_norm": placement["goal_h_norm"],
            "corner_zone": placement["corner_zone"],
            "placement_score": placement["placement_score"],
        })
    return pd.DataFrame(rows, columns=_DETAIL_COLUMNS)


def penalty_taker_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Per-taker penalty record: attempts, result breakdown, conversion
    rate, and average placement score (distance from the goal frame's
    center -- a "how close to the corners, on average" proxy for shot
    selection, not accuracy: a well-placed miss still counts as missed).
    """
    detail = penalty_placement_detail(events)
    columns = [
        "playerId", "playerName", "contestantId", "attempts", "goals",
        "saved", "post", "missed", "conversion_rate", "avg_placement_score",
    ]
    if detail.empty:
        return pd.DataFrame(columns=columns)

    out = (
        detail.groupby(["playerId", "playerName", "contestantId"], dropna=False)
        .agg(
            attempts=("eventId", "count"),
            goals=("result", lambda s: int((s == "scored").sum())),
            saved=("result", lambda s: int((s == "saved").sum())),
            post=("result", lambda s: int((s == "post").sum())),
            missed=("result", lambda s: int((s == "missed").sum())),
            avg_placement_score=("placement_score", "mean"),
        )
        .reset_index()
    )
    out["conversion_rate"] = (out["goals"] / out["attempts"]).round(3)
    out["avg_placement_score"] = out["avg_placement_score"].round(3)
    return out[columns].sort_values("attempts", ascending=False).reset_index(drop=True)
