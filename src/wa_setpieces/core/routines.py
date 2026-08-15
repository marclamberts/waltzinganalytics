"""Type-specific routine features for every supported set-piece restart.

The classifiers are transparent event-data heuristics. They describe *how* a
restart was taken (distance, direction, target area and routine family) while
the existing metrics modules describe what happened afterwards.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import constants as c
from .chains import link_set_piece_shots
from .filters import tag_set_pieces
from .retention import retention_detail


def _third(x: float) -> str | None:
    if pd.isna(x):
        return None
    return "defensive" if x < 100 / 3 else "middle" if x < 200 / 3 else "attacking"


def _channel(y: float) -> str | None:
    if pd.isna(y):
        return None
    if y < 20: return "right_wide"
    if y < 40: return "right_half_space"
    if y <= 60: return "central"
    if y <= 80: return "left_half_space"
    return "left_wide"


def _routine_type(row: pd.Series, set_piece_type: str) -> str:
    distance = row.get("distance")
    dx = row.get("progression")
    end_x = row.get("end_x")
    end_y = row.get("end_y")
    if set_piece_type == "penalty":
        if row["typeId"] == c.TYPE_GOAL: return "scored"
        if row["typeId"] == c.TYPE_ATTEMPT_SAVED: return "saved"
        if row["typeId"] == c.TYPE_POST: return "post"
        return "missed"
    if set_piece_type == "corner":
        if distance <= 12: return "short"
        if end_x >= 88 and 36 <= end_y <= 64: return "central_six_yard"
        if end_x >= 82 and 22 <= end_y <= 78: return "penalty_area"
        if dx < -5: return "recycled"
        return "deep_or_edge"
    if set_piece_type == "free_kick":
        if row["typeId"] in c.SHOT_TYPE_IDS: return "direct_shot"
        if distance <= 10: return "short"
        if end_x >= 80 and 18 <= end_y <= 82: return "box_delivery"
        if dx >= 15: return "progressive"
        if dx < -3: return "recycled"
        return "lateral"
    if set_piece_type == "throw_in":
        if distance <= 10: return "short"
        if distance <= 25: return "medium"
        return "long"
    if set_piece_type == "goal_kick":
        if distance <= 20: return "short_build"
        if distance <= 40: return "medium_build"
        return "long"
    if set_piece_type == "kick_off":
        if dx < -3: return "backward"
        if abs(dx) <= 3: return "lateral"
        if distance <= 15: return "short_forward"
        return "direct_long"
    return "other"


def restart_routines(
    events: pd.DataFrame, set_piece_type: str, *, retention_window_seconds: float = 8.0
) -> pd.DataFrame:
    """Return one feature-rich row per restart of ``set_piece_type``.

    Coordinates use the provider-neutral attacking frame (x increases toward
    goal). Distance is in Opta pitch units, direction is forward/backward/
    lateral, and ``routine_type`` applies the type-specific taxonomy documented
    in this module. Thresholds are descriptive defaults, not learned labels.
    """
    if set_piece_type not in c.SET_PIECE_TYPES:
        raise ValueError(f"set_piece_type must be one of {c.SET_PIECE_TYPES}")
    tagged = tag_set_pieces(events)
    restarts = tagged.loc[tagged["set_piece_type"] == set_piece_type].copy()
    if restarts.empty:
        return pd.DataFrame(columns=["eventId", "contestantId", "set_piece_type", "routine_type"])
    end_x_col, end_y_col = f"q_{c.QUALIFIER_PASS_END_X}", f"q_{c.QUALIFIER_PASS_END_Y}"
    restarts["end_x"] = pd.to_numeric(restarts[end_x_col], errors="coerce") if end_x_col in restarts else np.nan
    restarts["end_y"] = pd.to_numeric(restarts[end_y_col], errors="coerce") if end_y_col in restarts else np.nan
    restarts["progression"] = restarts["end_x"] - pd.to_numeric(restarts["x"], errors="coerce")
    restarts["lateral_change"] = restarts["end_y"] - pd.to_numeric(restarts["y"], errors="coerce")
    restarts["distance"] = np.hypot(restarts["progression"], restarts["lateral_change"])
    restarts["direction"] = np.select(
        [restarts["progression"] > 3, restarts["progression"] < -3],
        ["forward", "backward"], default="lateral",
    )
    restarts["start_third"] = restarts["x"].map(_third)
    restarts["end_third"] = restarts["end_x"].map(_third)
    restarts["start_channel"] = restarts["y"].map(_channel)
    restarts["target_channel"] = restarts["end_y"].map(_channel)
    restarts["side"] = np.select([restarts["y"] < 40, restarts["y"] > 60], ["right", "left"], default="central")
    restarts["successful"] = pd.to_numeric(restarts["outcome"], errors="coerce").fillna(0).eq(1)
    restarts["routine_type"] = restarts.apply(_routine_type, axis=1, set_piece_type=set_piece_type)

    linked = link_set_piece_shots(events)
    produced = linked.loc[linked["set_piece_type"] == set_piece_type].groupby(
        ["contestantId", "set_piece_event_id"], as_index=False
    ).agg(shots=("eventId", "count"), goals=("is_goal", "sum"))
    restarts = restarts.merge(produced, left_on=["contestantId", "eventId"], right_on=["contestantId", "set_piece_event_id"], how="left")
    restarts["shots"] = restarts["shots"].fillna(0).astype(int)
    restarts["goals"] = restarts["goals"].fillna(0).astype(int)
    restarts = restarts.drop(columns="set_piece_event_id", errors="ignore")
    if set_piece_type != "penalty":
        retained = retention_detail(events, set_piece_type, window_seconds=retention_window_seconds)
        restarts = restarts.merge(retained[["contestantId", "eventId", "retained"]], on=["contestantId", "eventId"], how="left")
    else:
        restarts["retained"] = pd.NA
    columns = [
        "eventId", "contestantId", "playerId", "playerName", "set_piece_type", "routine_type",
        "x", "y", "end_x", "end_y", "distance", "progression", "lateral_change", "direction",
        "side", "start_third", "end_third", "start_channel", "target_channel", "successful",
        "retained", "shots", "goals", "timeMin", "timeSec",
    ]
    return restarts[columns].reset_index(drop=True)


def routine_summary(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """Aggregate routine usage and outcomes by team and routine family."""
    detail = restart_routines(events, set_piece_type, **kwargs)
    if detail.empty:
        return pd.DataFrame(columns=["contestantId", "routine_type", "attempts"])
    out = detail.groupby(["contestantId", "routine_type"], as_index=False).agg(
        attempts=("eventId", "count"), successful=("successful", "sum"),
        retained=("retained", "sum"), shots=("shots", "sum"), goals=("goals", "sum"),
        avg_distance=("distance", "mean"), avg_progression=("progression", "mean"),
    )
    team_total = out.groupby("contestantId")["attempts"].transform("sum")
    out["usage_share"] = (out["attempts"] / team_total).round(3)
    out["success_rate"] = (out["successful"] / out["attempts"]).round(3)
    out["retention_rate"] = (out["retained"] / out["attempts"]).round(3)
    out["shot_rate"] = (out["shots"] / out["attempts"]).round(3)
    out["avg_distance"] = out["avg_distance"].round(2)
    out["avg_progression"] = out["avg_progression"].round(2)
    return out


def all_routine_summaries(events: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Combine routine summaries for all six supported restart types."""
    frames = [routine_summary(events, kind, **kwargs).assign(set_piece_type=kind) for kind in c.SET_PIECE_TYPES]
    frames = [frame for frame in frames if not frame.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
