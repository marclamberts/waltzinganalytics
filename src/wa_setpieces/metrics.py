"""Aggregate set-piece metrics: counts, success rates, delivery, and shot/goal
output, by team and by player.
"""

from __future__ import annotations

import pandas as pd

from . import constants as c
from .chains import link_set_piece_shots
from .filters import tag_set_pieces


def _success(events: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(events["outcome"], errors="coerce").fillna(0) == 1


def team_set_piece_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Per team, per set-piece type: attempts and success rate.

    "Success" follows Opta's ``outcome`` flag on the restart pass itself
    (e.g. for a throw-in, whether it was retained by the throwing team).
    """
    tagged = tag_set_pieces(events)
    sp = tagged.loc[tagged["set_piece_type"].notna()].copy()
    if sp.empty:
        return pd.DataFrame(
            columns=["contestantId", "set_piece_type", "attempts", "successful", "success_rate"]
        )
    sp["successful"] = _success(sp)
    out = (
        sp.groupby(["contestantId", "set_piece_type"])
        .agg(attempts=("eventId", "count"), successful=("successful", "sum"))
        .reset_index()
    )
    out["success_rate"] = (out["successful"] / out["attempts"]).round(3)
    return out


def player_set_piece_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Per player, per set-piece type: attempts and success rate."""
    tagged = tag_set_pieces(events)
    sp = tagged.loc[tagged["set_piece_type"].notna() & tagged["playerId"].notna()].copy()
    if sp.empty:
        return pd.DataFrame(
            columns=[
                "playerId",
                "playerName",
                "contestantId",
                "set_piece_type",
                "attempts",
                "successful",
                "success_rate",
            ]
        )
    sp["successful"] = _success(sp)
    out = (
        sp.groupby(["playerId", "playerName", "contestantId", "set_piece_type"])
        .agg(attempts=("eventId", "count"), successful=("successful", "sum"))
        .reset_index()
    )
    out["success_rate"] = (out["successful"] / out["attempts"]).round(3)
    return out


def delivery_locations(events: pd.DataFrame, set_piece_type: str) -> pd.DataFrame:
    """Start/end pitch coordinates for one set-piece type (for maps/heatmaps).

    ``set_piece_type`` must be one of the pass-based types: "corner",
    "free_kick", "throw_in", "goal_kick" or "kick_off" (penalties have no
    end location, they are a shot).

    Returns columns: eventId, contestantId, playerId, playerName, x, y,
    end_x, end_y, outcome.
    """
    if set_piece_type not in c.SET_PIECE_QUALIFIERS:
        raise ValueError(
            f"set_piece_type must be one of {sorted(c.SET_PIECE_QUALIFIERS)}, "
            f"got {set_piece_type!r}"
        )
    tagged = tag_set_pieces(events)
    sp = tagged.loc[tagged["set_piece_type"] == set_piece_type].copy()
    end_x_col = f"q_{c.QUALIFIER_PASS_END_X}"
    end_y_col = f"q_{c.QUALIFIER_PASS_END_Y}"
    sp["end_x"] = pd.to_numeric(sp.get(end_x_col), errors="coerce")
    sp["end_y"] = pd.to_numeric(sp.get(end_y_col), errors="coerce")
    return sp[
        ["eventId", "contestantId", "playerId", "playerName", "x", "y", "end_x", "end_y", "outcome"]
    ].reset_index(drop=True)


def set_piece_summary(events: pd.DataFrame) -> pd.DataFrame:
    """One row per (team, set-piece type): attempts, success rate, shots, goals.

    This is the main "headline numbers" table: how often each team used
    each restart type, how often it kept the ball / won the duel, and how
    often that restart directly produced a shot or a goal (via the assist
    chain in :mod:`wa_setpieces.chains`).
    """
    counts = team_set_piece_counts(events)
    if counts.empty:
        return counts.assign(shots=[], goals=[])

    linked = link_set_piece_shots(events)
    from_sp = linked.loc[linked["set_piece_type"].notna()]
    shots = (
        from_sp.groupby(["contestantId", "set_piece_type"])
        .size()
        .rename("shots")
        .reset_index()
    )
    goals = (
        from_sp.loc[from_sp["is_goal"]]
        .groupby(["contestantId", "set_piece_type"])
        .size()
        .rename("goals")
        .reset_index()
    )

    out = counts.merge(shots, on=["contestantId", "set_piece_type"], how="left")
    out = out.merge(goals, on=["contestantId", "set_piece_type"], how="left")
    out["shots"] = out["shots"].fillna(0).astype(int)
    out["goals"] = out["goals"].fillna(0).astype(int)
    return out
