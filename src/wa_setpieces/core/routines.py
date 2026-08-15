"""Type-specific routine features for every supported set-piece restart.

The classifiers are transparent event-data heuristics. They describe *how* a
restart was taken (distance, direction, target area and routine family) while
the existing metrics modules describe what happened afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def _destination_zone(x: float, y: float) -> str | None:
    if pd.isna(x) or pd.isna(y): return None
    if x >= 94 and 37 <= y <= 63: return "six_yard_box"
    if x >= 83 and 21 <= y <= 79: return "penalty_area"
    if 75 <= x < 83 and 21 <= y <= 79: return "box_edge"
    if x >= 83: return "wide_final_third"
    return f"{_third(x)}_{_channel(y)}"


def _outcome_category(row: pd.Series) -> str:
    if row["goals"] > 0: return "goal"
    if row["shots"] > 0: return "shot"
    if row.get("retained") is True or row.get("retained") == np.True_: return "retained"
    if row["successful"]: return "successful_first_action"
    return "lost"


def _restart_routines_single(
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
    # Approximate physical geometry using a 105x68m pitch while retaining the
    # native 0..100 values alongside it.
    dx_m = restarts["progression"] * 1.05
    dy_m = restarts["lateral_change"] * 0.68
    restarts["distance_m"] = np.hypot(dx_m, dy_m)
    restarts["angle_degrees"] = np.degrees(np.arctan2(dy_m, dx_m))
    restarts["verticality"] = np.where(restarts["distance_m"] > 0, dx_m / restarts["distance_m"], np.nan)
    restarts["direction"] = np.select(
        [restarts["progression"] > 3, restarts["progression"] < -3],
        ["forward", "backward"], default="lateral",
    )
    restarts["start_third"] = restarts["x"].map(_third)
    restarts["end_third"] = restarts["end_x"].map(_third)
    restarts["start_channel"] = restarts["y"].map(_channel)
    restarts["target_channel"] = restarts["end_y"].map(_channel)
    restarts["destination_zone"] = [_destination_zone(x, y) for x, y in zip(restarts["end_x"], restarts["end_y"])]
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
    restarts["outcome_category"] = restarts.apply(_outcome_category, axis=1)
    restarts["routine_key"] = (
        restarts["routine_type"].fillna("unknown") + "|" +
        restarts["side"].fillna("unknown") + "|" +
        restarts["destination_zone"].fillna("unknown")
    )
    columns = [
        "eventId", "contestantId", "playerId", "playerName", "set_piece_type", "routine_type",
        "x", "y", "end_x", "end_y", "distance", "distance_m", "progression", "lateral_change",
        "angle_degrees", "verticality", "direction", "side", "start_third", "end_third",
        "start_channel", "target_channel", "destination_zone", "successful", "retained", "shots",
        "goals", "outcome_category", "routine_key", "timeMin", "timeSec",
    ]
    return restarts[columns].reset_index(drop=True)


def restart_routines(
    events: pd.DataFrame, set_piece_type: str, *, retention_window_seconds: float = 8.0
) -> pd.DataFrame:
    """Match-safe routine detail for one restart type.

    When ``matchId`` is present each match is analysed independently, preventing
    event IDs and temporal windows from crossing match boundaries.
    """
    if "matchId" not in events.columns:
        return _restart_routines_single(events, set_piece_type, retention_window_seconds=retention_window_seconds)
    frames = []
    for match_id, frame in events.groupby("matchId", sort=False):
        detail = _restart_routines_single(frame.drop(columns="matchId"), set_piece_type, retention_window_seconds=retention_window_seconds)
        detail.insert(0, "matchId", match_id)
        frames.append(detail)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


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


def routine_team_profiles(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """One tactical profile per team, including variety and predictability."""
    detail = restart_routines(events, set_piece_type, **kwargs)
    if detail.empty: return pd.DataFrame()
    rows = []
    for team, group in detail.groupby("contestantId"):
        shares = group["routine_key"].value_counts(normalize=True)
        entropy = float(-(shares * np.log2(shares)).sum()) if len(shares) else 0.0
        max_entropy = np.log2(len(shares)) if len(shares) > 1 else 0.0
        rows.append({
            "contestantId": team, "set_piece_type": set_piece_type, "attempts": len(group),
            "routine_families": group["routine_type"].nunique(), "distinct_patterns": len(shares),
            "most_used_routine": group["routine_type"].mode().iat[0],
            "most_used_pattern": shares.index[0], "top_pattern_share": round(float(shares.iloc[0]), 3),
            "routine_diversity": round(entropy / max_entropy, 3) if max_entropy else 0.0,
            "success_rate": round(float(group["successful"].mean()), 3),
            "retention_rate": round(float(group["retained"].fillna(False).mean()), 3),
            "shot_rate": round(float(group["shots"].gt(0).mean()), 3),
            "goal_rate": round(float(group["goals"].gt(0).mean()), 3),
            "avg_distance_m": round(float(group["distance_m"].mean()), 2),
            "avg_progression": round(float(group["progression"].mean()), 2),
        })
    return pd.DataFrame(rows)


def routine_taker_profiles(events: pd.DataFrame, set_piece_type: str, min_attempts: int = 1, **kwargs) -> pd.DataFrame:
    """Per-taker volume, preference and result profile."""
    detail = restart_routines(events, set_piece_type, **kwargs)
    if detail.empty: return pd.DataFrame()
    detail = detail.loc[detail["playerId"].notna()]
    if detail.empty: return pd.DataFrame()
    rows = []
    for keys, group in detail.groupby(["playerId", "playerName", "contestantId"], dropna=False):
        if len(group) < min_attempts: continue
        mix = group["routine_type"].value_counts(normalize=True)
        rows.append({
            "playerId": keys[0], "playerName": keys[1], "contestantId": keys[2],
            "set_piece_type": set_piece_type, "attempts": len(group),
            "preferred_routine": mix.index[0], "preferred_routine_share": round(float(mix.iloc[0]), 3),
            "routine_families": len(mix), "success_rate": round(float(group["successful"].mean()), 3),
            "retention_rate": round(float(group["retained"].fillna(False).mean()), 3),
            "shots_created": int(group["shots"].sum()), "goals_created": int(group["goals"].sum()),
            "avg_distance_m": round(float(group["distance_m"].mean()), 2),
            "avg_progression": round(float(group["progression"].mean()), 2),
        })
    return pd.DataFrame(rows).sort_values("attempts", ascending=False).reset_index(drop=True) if rows else pd.DataFrame()


def routine_target_matrix(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """Long-form routine-to-destination matrix with usage and outcomes."""
    detail = restart_routines(events, set_piece_type, **kwargs)
    if detail.empty: return pd.DataFrame()
    known = detail.dropna(subset=["destination_zone"])
    if known.empty: return pd.DataFrame()
    out = known.groupby(["contestantId", "routine_type", "destination_zone"], as_index=False).agg(
        attempts=("eventId", "count"), successful=("successful", "sum"), shots=("shots", "sum"), goals=("goals", "sum")
    )
    totals = out.groupby("contestantId")["attempts"].transform("sum")
    out["team_usage_share"] = (out["attempts"] / totals).round(3)
    out["success_rate"] = (out["successful"] / out["attempts"]).round(3)
    out["shot_rate"] = (out["shots"] / out["attempts"]).round(3)
    return out


@dataclass
class RoutineAnalysis:
    set_piece_type: str
    detail: pd.DataFrame
    summary: pd.DataFrame
    team_profiles: pd.DataFrame
    taker_profiles: pd.DataFrame
    target_matrix: pd.DataFrame


def analyze_routines(events: pd.DataFrame, set_piece_type: str, *, min_taker_attempts: int = 1, **kwargs) -> RoutineAnalysis:
    """Build the complete structured routine-analysis bundle."""
    return RoutineAnalysis(
        set_piece_type=set_piece_type,
        detail=restart_routines(events, set_piece_type, **kwargs),
        summary=routine_summary(events, set_piece_type, **kwargs),
        team_profiles=routine_team_profiles(events, set_piece_type, **kwargs),
        taker_profiles=routine_taker_profiles(events, set_piece_type, min_attempts=min_taker_attempts, **kwargs),
        target_matrix=routine_target_matrix(events, set_piece_type, **kwargs),
    )
