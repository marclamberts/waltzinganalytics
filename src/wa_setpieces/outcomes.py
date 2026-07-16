"""Classify what happened right after a corner/free-kick delivery into one
discrete outcome category, for a shot-map-style scatter of results.

This builds on :mod:`wa_setpieces.phases` (a derived heuristic -- same
caveats apply) and adds two things phases.py doesn't track on its own:

- **short_corner**: the delivery itself was played short (a pass to a
  nearby teammate rather than a cross into the box), inferred from the
  delivery's own start/end distance being small -- see
  :data:`DEFAULT_SHORT_CORNER_MAX_DISTANCE`. Distance alone, not end
  position: a corner starts right at the corner arc (``x`` around 99-100),
  so even a real short corner played along the byline barely moves ``x``
  at all (it moves in ``y``, hugging the touchline) -- an end-position
  threshold and a short-distance threshold turn out to be nearly mutually
  exclusive from that starting point (confirmed: requiring both ``x`` to
  drop below 85 *and* distance under 15 leaves under half a unit of
  overlap, and any sideways component removes it entirely).
- **aerial_duel** ("50/50"): the first contact after the delivery is an
  aerial duel (``typeId`` 44, confirmed in the F24 spec) -- a contested
  header, regardless of which team's event actually recorded the win/loss,
  since in football terms a challenged header stays a "50/50" moment.

Everything else falls out of :func:`~wa_setpieces.phases.classify_phase`'s
own fields: ``direct_shot`` (a shot straight off the delivery),
``second_phase_shot`` (a shot after a loose ball), ``cleared_immediately``
(the defending team's first touch sends it well clear), or otherwise
whichever team wins the first touch (``first_touch_won`` /
``first_touch_lost``) without fully resolving the phase.

Categories are checked in a fixed priority order per delivery (a delivery
only ever gets one label): short_corner > direct_shot > second_phase_shot
> aerial_duel > cleared > first_touch_lost > first_touch_won > no_action.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import constants as c
from .filters import extract_corners, extract_free_kicks
from .phases import (
    DEFAULT_CLEAR_SAFE_X,
    DEFAULT_MAX_EVENTS,
    DEFAULT_MAX_GAP_SECONDS,
    DEFAULT_MAX_TOTAL_SECONDS,
    classify_phase,
)
from .zones import to_reference_frame

DEFAULT_SHORT_CORNER_MAX_DISTANCE = 12.0

OUTCOME_CATEGORIES = (
    "short_corner",
    "direct_shot",
    "second_phase_shot",
    "aerial_duel",
    "cleared",
    "first_touch_lost",
    "first_touch_won",
    "no_action",
)

_EXTRACTORS = {"corner": extract_corners, "free_kick": extract_free_kicks}


def _is_short_corner(delivery_row: pd.Series, max_distance: float) -> bool:
    end_x = delivery_row.get(f"q_{c.QUALIFIER_PASS_END_X}")
    end_y = delivery_row.get(f"q_{c.QUALIFIER_PASS_END_Y}")
    if end_x is None or end_y is None:
        return False
    try:
        end_x, end_y = float(end_x), float(end_y)
    except (TypeError, ValueError):
        return False
    distance = float(np.hypot(end_x - float(delivery_row["x"]), end_y - float(delivery_row["y"])))
    return distance < max_distance


def _event_xy_in_attacking_frame(
    events: pd.DataFrame, contestant_id: str, event_id, attacking_team: str
):
    row = events.loc[
        (events["contestantId"] == contestant_id) & (events["eventId"] == event_id)
    ]
    if row.empty:
        return None, None
    row = row.iloc[[0]]
    if contestant_id != attacking_team:
        row = to_reference_frame(row, attacking_team)
    return float(row.iloc[0]["x"]), float(row.iloc[0]["y"])


def classify_delivery_outcome(
    events: pd.DataFrame,
    delivery_row: pd.Series,
    short_corner_max_distance: float = DEFAULT_SHORT_CORNER_MAX_DISTANCE,
    clear_safe_x: float = DEFAULT_CLEAR_SAFE_X,
    max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
    max_total_seconds: float = DEFAULT_MAX_TOTAL_SECONDS,
    max_events: int = DEFAULT_MAX_EVENTS,
) -> dict:
    """Classify one delivery's outcome. See module docstring for the categories.

    Returns:
        A dict: ``delivery_event_id``, ``set_piece_type``, ``contestantId``,
        ``playerId``, ``playerName``, ``category``, ``x``, ``y`` (the plot
        location for that category -- see module docstring for which event
        each category's location comes from), ``is_goal``.
    """
    set_piece_type = delivery_row.get("set_piece_type")
    attacking_team = delivery_row["contestantId"]
    base = {
        "delivery_event_id": delivery_row["eventId"],
        "set_piece_type": set_piece_type,
        "contestantId": attacking_team,
        "playerId": delivery_row.get("playerId"),
        "playerName": delivery_row.get("playerName"),
        "is_goal": False,
    }

    if set_piece_type == "corner" and _is_short_corner(delivery_row, short_corner_max_distance):
        return {
            **base,
            "category": "short_corner",
            "x": float(delivery_row[f"q_{c.QUALIFIER_PASS_END_X}"]),
            "y": float(delivery_row[f"q_{c.QUALIFIER_PASS_END_Y}"]),
        }

    result = classify_phase(
        events,
        delivery_row,
        clear_safe_x=clear_safe_x,
        max_gap_seconds=max_gap_seconds,
        max_total_seconds=max_total_seconds,
        max_events=max_events,
    )

    if result.direct_shot:
        x, y = _event_xy_in_attacking_frame(
            events, attacking_team, result.direct_shot_event_id, attacking_team
        )
        return {**base, "category": "direct_shot", "x": x, "y": y, "is_goal": result.direct_shot_is_goal}

    if result.second_phase_shot:
        x, y = _event_xy_in_attacking_frame(
            events, attacking_team, result.second_phase_event_id, attacking_team
        )
        return {
            **base, "category": "second_phase_shot", "x": x, "y": y,
            "is_goal": result.second_phase_is_goal,
        }

    if result.first_contact_event_id is None:
        # Nothing happened in the window at all (e.g. period ended).
        return {
            **base, "category": "no_action",
            "x": float(delivery_row.get(f"q_{c.QUALIFIER_PASS_END_X}", delivery_row["x"]) or delivery_row["x"]),
            "y": float(delivery_row.get(f"q_{c.QUALIFIER_PASS_END_Y}", delivery_row["y"]) or delivery_row["y"]),
        }

    x, y = _event_xy_in_attacking_frame(
        events, result.first_contact_team, result.first_contact_event_id, attacking_team
    )

    if result.first_contact_type_id == c.TYPE_AERIAL:
        category = "aerial_duel"
    elif result.cleared_immediately:
        category = "cleared"
    elif result.first_contact_team == result.opponent_id:
        category = "first_touch_lost"
    else:
        category = "first_touch_won"

    return {**base, "category": category, "x": x, "y": y}


def delivery_outcomes(
    events: pd.DataFrame,
    set_piece_type: str,
    **kwargs,
) -> pd.DataFrame:
    """:func:`classify_delivery_outcome` for every delivery of one set-piece type.

    Args:
        set_piece_type: ``"corner"`` or ``"free_kick"``.
        **kwargs: forwarded to :func:`classify_delivery_outcome` (e.g.
            ``clear_safe_x``, ``short_corner_max_distance``).

    Returns:
        One row per delivery: delivery_event_id, set_piece_type,
        contestantId, playerId, playerName, category, x, y, is_goal.
    """
    if set_piece_type not in _EXTRACTORS:
        raise ValueError(
            f"set_piece_type must be one of {sorted(_EXTRACTORS)}, got {set_piece_type!r}"
        )
    deliveries = _EXTRACTORS[set_piece_type](events)
    records = []
    for _, delivery_row in deliveries.iterrows():
        delivery_row = delivery_row.copy()
        delivery_row["set_piece_type"] = set_piece_type
        records.append(classify_delivery_outcome(events, delivery_row, **kwargs))
    columns = [
        "delivery_event_id", "set_piece_type", "contestantId", "playerId",
        "playerName", "category", "x", "y", "is_goal",
    ]
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame.from_records(records, columns=columns)


def outcome_summary(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """Per-team counts of each outcome category (see :data:`OUTCOME_CATEGORIES`)."""
    outcomes = delivery_outcomes(events, set_piece_type, **kwargs)
    if outcomes.empty:
        return pd.DataFrame(columns=["contestantId", "category", "count"])
    return (
        outcomes.groupby(["contestantId", "category"])
        .size()
        .rename("count")
        .reset_index()
    )
