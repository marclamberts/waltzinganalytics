"""Defensive set-piece metrics, calculated match-by-match."""

from __future__ import annotations

import pandas as pd

from .metrics import set_piece_summary


def defensive_set_piece_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Return set-piece attempts, shots and goals conceded by defending team.

    Multi-match input must carry ``matchId``. Matches with anything other than
    two contestants are rejected because the opponent cannot be inferred
    unambiguously.
    """
    group_key = "matchId" if "matchId" in events.columns else None
    matches = events.groupby(group_key, sort=False) if group_key else [("match", events)]
    frames = []
    for match_id, frame in matches:
        teams = frame["contestantId"].dropna().unique().tolist()
        if len(teams) != 2:
            raise ValueError(f"match {match_id!r} must contain exactly two contestants")
        attacking = set_piece_summary(frame)
        opponent = {teams[0]: teams[1], teams[1]: teams[0]}
        attacking["contestantId"] = attacking["contestantId"].map(opponent)
        attacking = attacking.rename(columns={
            "attempts": "attempts_faced", "successful": "opponent_successful",
            "success_rate": "opponent_success_rate", "shots": "shots_conceded",
            "goals": "goals_conceded",
        })
        attacking["matchId"] = match_id
        frames.append(attacking)
    if not frames:
        return pd.DataFrame()
    detail = pd.concat(frames, ignore_index=True)
    out = detail.groupby(["contestantId", "set_piece_type"], as_index=False).agg(
        matches=("matchId", "nunique"), attempts_faced=("attempts_faced", "sum"),
        opponent_successful=("opponent_successful", "sum"),
        shots_conceded=("shots_conceded", "sum"), goals_conceded=("goals_conceded", "sum"),
    )
    out["opponent_success_rate"] = (out["opponent_successful"] / out["attempts_faced"]).round(3)
    out["shots_conceded_per_100"] = (100 * out["shots_conceded"] / out["attempts_faced"]).round(2)
    return out


def defensive_rating(summary: pd.DataFrame) -> pd.DataFrame:
    """Benchmark defensive outcomes on 0..100, with lower concessions better."""
    from .rating import _zscore_to_100

    required = {"opponent_success_rate", "shots_conceded_per_100", "goals_conceded"}
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"missing defensive metrics: {sorted(missing)}")
    out = summary.copy()
    metrics = []
    for column in sorted(required):
        score = f"{column}_score"
        out[score] = _zscore_to_100(-pd.to_numeric(out[column], errors="coerce"))
        metrics.append(score)
    out["rating"] = out[metrics].mean(axis=1).round(1)
    return out
