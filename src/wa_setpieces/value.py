"""Set-piece added value: one number blending delivery threat and shot quality.

:mod:`wa_setpieces.xt` already answers "how much more dangerous did the
delivery make the ball position" (``xt_added``). This module adds the other
half: if that delivery produced a shot -- whether straight off the ball or
via a second-phase loose ball -- how good a chance was it, and did it
actually end in a goal.

The link between a delivery and "its" shot comes from
:func:`wa_setpieces.chains.link_set_piece_shots`, which follows Opta's own
assist-chain qualifier rather than a positional heuristic -- more reliable
than re-deriving it, since it's the provider's own data. This is a
different (and stricter) definition of "resulted in a shot" than
:mod:`wa_setpieces.phases`' second-phase detection, which infers phases
from event sequencing when there's no assist qualifier to follow; the two
won't always agree on borderline cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .chains import link_set_piece_shots
from .metrics import delivery_locations
from .xt import XTModel


def set_piece_added_value(
    events: pd.DataFrame, set_piece_type: str, model: XTModel
) -> pd.DataFrame:
    """Per-delivery value: xT added by the delivery, plus the quality of any
    shot it produced, plus whether that shot was a goal.

    Args:
        set_piece_type: ``"corner"`` or ``"free_kick"`` (a pass-based set
            piece with start/end coordinates -- see
            :func:`~wa_setpieces.delivery_locations`).
        model: a fitted :class:`~wa_setpieces.XTModel` (must come from
            :meth:`XTModel.fit`, not :meth:`XTModel.from_csv` -- shot value
            needs the shot/goal probability grids, which aren't persisted).

    Returns:
        One row per delivery: eventId, contestantId, playerId, playerName,
        outcome, delivery_xt_added, shot_value, added_value, is_goal.

        ``delivery_xt_added`` is 0 (not NaN) here when the delivery didn't
        find a teammate -- unlike :func:`~wa_setpieces.xt.set_piece_delivery_xt`,
        which leaves it NaN, this module needs a summable number so an
        unsuccessful delivery that somehow still produced a shot (e.g. a
        half-cleared corner an teammate reacts to) doesn't drop out of the
        total. ``shot_value`` is 0 when no shot resulted from the delivery.
        ``added_value = delivery_xt_added + shot_value``.
    """
    deliveries = delivery_locations(events, set_piece_type)
    shots = link_set_piece_shots(events)
    # Indexed by (contestantId, set_piece_event_id): eventId is only unique
    # within one team's own event stream (see chains.py's docstring), so a
    # delivery's shot must be looked up scoped to its own team too -- an
    # eventId-only index could otherwise match another team's shot that
    # happens to share the same delivery's eventId number.
    shots_by_delivery = (
        shots.dropna(subset=["set_piece_event_id"])
        .astype({"set_piece_event_id": int})
        .set_index(["contestantId", "set_piece_event_id"])
    )

    xt_start = model.value_series(deliveries["x"], deliveries["y"])
    xt_end = model.value_series(deliveries["end_x"], deliveries["end_y"])
    successful = pd.to_numeric(deliveries["outcome"], errors="coerce").fillna(0) == 1
    delivery_xt_added = np.where(successful, (xt_end - xt_start).fillna(0), 0.0)

    shot_value = np.zeros(len(deliveries))
    is_goal = np.zeros(len(deliveries), dtype=bool)
    for i, (contestant_id, event_id) in enumerate(
        zip(deliveries["contestantId"].to_numpy(), deliveries["eventId"].to_numpy())
    ):
        key = (contestant_id, event_id)
        if key not in shots_by_delivery.index:
            continue
        row = shots_by_delivery.loc[key]
        if isinstance(row, pd.DataFrame):  # defensive; shouldn't occur
            row = row.iloc[0]
        shot_value[i] = model.shot_value(row["x"], row["y"])
        is_goal[i] = bool(row["is_goal"])

    out = deliveries[["eventId", "contestantId", "playerId", "playerName", "outcome"]].copy()
    out["delivery_xt_added"] = delivery_xt_added
    out["shot_value"] = shot_value
    out["added_value"] = out["delivery_xt_added"] + out["shot_value"]
    out["is_goal"] = is_goal
    return out.reset_index(drop=True)


def set_piece_value_summary(
    events: pd.DataFrame, set_piece_type: str, model: XTModel
) -> pd.DataFrame:
    """Per-team roll-up of :func:`set_piece_added_value`.

    Returns: contestantId, deliveries, total_added_value, avg_added_value, goals.
    """
    detail = set_piece_added_value(events, set_piece_type, model)
    if detail.empty:
        return pd.DataFrame(
            columns=["contestantId", "deliveries", "total_added_value", "avg_added_value", "goals"]
        )
    out = (
        detail.groupby("contestantId")
        .agg(
            deliveries=("eventId", "count"),
            total_added_value=("added_value", "sum"),
            avg_added_value=("added_value", "mean"),
            goals=("is_goal", "sum"),
        )
        .reset_index()
    )
    out["total_added_value"] = out["total_added_value"].round(4)
    out["avg_added_value"] = out["avg_added_value"].round(4)
    return out
