"""Goal-mouth shot placement geometry, from Opta qualifiers 102 ("goal
mouth y") and 103 ("goal mouth z").

Shared by :mod:`wa_setpieces.ml.shot_value` (placement features for the
bundled shot-value models) and :mod:`wa_setpieces.core.penalties`
(penalty placement zone) -- pure geometry, no optional dependency needed
(unlike the trained models in :mod:`wa_setpieces.ml.shot_value`, which do
need the ``ml`` extra).

``goal_y_norm`` is confirmed by its value range (spans well outside the
goal-post band for shots that missed wide, consistent with a
whole-pitch-width coordinate). ``goal_h_norm`` additionally assumes
qualifier 103 is on a 0-38 scale (38 = crossbar), a figure seen in other
open-source Opta parsers but not independently confirmed here -- treat it
as a reasonable placeholder, not ground truth, same caveat
:mod:`wa_setpieces.ml.shot_value`'s module docstring gives its own
placement features.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PITCH_WIDTH_M = 68.0
GOAL_WIDTH_M = 7.32
GOAL_HEIGHT_QUALIFIER_MAX = 38.0  # unconfirmed assumption, see module docstring

GOAL_Y_LOW = 50.0 - (GOAL_WIDTH_M / PITCH_WIDTH_M * 100.0) / 2.0
GOAL_Y_HIGH = 50.0 + (GOAL_WIDTH_M / PITCH_WIDTH_M * 100.0) / 2.0

QUALIFIER_GOAL_MOUTH_Y = 102
QUALIFIER_GOAL_MOUTH_Z = 103


def goal_placement(raw_event: pd.Series) -> dict:
    """Placement features from qualifierId 102/103 on a shot event.

    ``raw_event`` is a row from :func:`~wa_setpieces.load_events`'s events
    DataFrame, where each qualifier is already flattened to a ``q_<id>``
    column (see :class:`wa_setpieces.core.loader.Match`).

    Returns a dict: ``is_deflected`` (always 0 -- no reliable qualifier
    signal, see :mod:`wa_setpieces.ml.shot_value`), ``goal_y_norm``,
    ``goal_h_norm`` (0-1 normalized position across/up the goal frame,
    ``NaN`` if the qualifiers aren't present), ``goal_frame_dist`` (0 if
    inside the frame, else how far wide/high it missed), ``corner_zone``
    (0-8, a 3x3 grid over the goal frame, row-major bottom-left to
    top-right; -1 if placement is unknown), ``placement_score`` (distance
    from the frame's center -- a simple "hardest to save" proxy, corners
    score higher).
    """
    goal_y_raw = raw_event.get(f"q_{QUALIFIER_GOAL_MOUTH_Y}")
    goal_z_raw = raw_event.get(f"q_{QUALIFIER_GOAL_MOUTH_Z}")

    goal_y_norm = float("nan")
    goal_h_norm = float("nan")
    if goal_y_raw is not None:
        try:
            goal_y_norm = (float(goal_y_raw) - GOAL_Y_LOW) / (GOAL_Y_HIGH - GOAL_Y_LOW)
        except (TypeError, ValueError):
            pass
    if goal_z_raw is not None:
        try:
            goal_h_norm = float(goal_z_raw) / GOAL_HEIGHT_QUALIFIER_MAX
        except (TypeError, ValueError):
            pass

    if np.isnan(goal_y_norm) or np.isnan(goal_h_norm):
        return dict(
            is_deflected=0, goal_y_norm=goal_y_norm, goal_h_norm=goal_h_norm,
            goal_frame_dist=float("nan"), corner_zone=-1, placement_score=float("nan"),
        )

    # Distance outside the goal frame (0 if inside it) -- how far wide/high
    # the placement missed, in normalized goal-width/height units.
    dx = max(0.0 - goal_y_norm, goal_y_norm - 1.0, 0.0)
    dy = max(0.0 - goal_h_norm, goal_h_norm - 1.0, 0.0)
    goal_frame_dist = float(np.hypot(dx, dy))

    # 3x3 grid over the goal frame (clamped to it even if the shot missed
    # wide, so "which zone was it *aimed* at" stays defined): 0=bottom-left
    # .. 8=top-right, row-major, matching a typical goal-frame heatmap.
    col = int(np.clip(goal_y_norm, 0.0, 0.999) * 3)
    row = int(np.clip(goal_h_norm, 0.0, 0.999) * 3)
    corner_zone = row * 3 + col

    # Simple "hardest to save" proxy: distance from goal center, in the
    # same normalized units -- corners of the frame score higher.
    placement_score = float(np.hypot(goal_y_norm - 0.5, goal_h_norm - 0.5))

    return dict(
        is_deflected=0, goal_y_norm=goal_y_norm, goal_h_norm=goal_h_norm,
        goal_frame_dist=goal_frame_dist, corner_zone=corner_zone,
        placement_score=placement_score,
    )
