"""Defensive set-piece metrics, calculated match-by-match."""

from __future__ import annotations

import pandas as pd

from .metrics import set_piece_summary
from .routines import restart_routines


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


def _conceded_routine_detail(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """:func:`~wa_setpieces.core.routines.restart_routines` detail, flipped to
    the defending team's perspective (``contestantId`` becomes the opponent
    who faced that routine), match-by-match like :func:`defensive_set_piece_summary`.
    """
    group_key = "matchId" if "matchId" in events.columns else None
    matches = events.groupby(group_key, sort=False) if group_key else [("match", events)]
    frames = []
    for match_id, frame in matches:
        teams = frame["contestantId"].dropna().unique().tolist()
        if len(teams) != 2:
            raise ValueError(f"match {match_id!r} must contain exactly two contestants")
        detail = restart_routines(frame, set_piece_type, **kwargs)
        if detail.empty:
            continue
        opponent = {teams[0]: teams[1], teams[1]: teams[0]}
        detail = detail.copy()
        detail["contestantId"] = detail["contestantId"].map(opponent)
        detail["matchId"] = match_id
        frames.append(detail)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def defensive_routine_summary(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """Per-team, per-routine-type: how many of that routine a team *conceded*,
    and the shots/goals it produced against them.

    Flips :func:`~wa_setpieces.core.routines.restart_routines`'s attacking
    perspective to answer "which routines is our defending most exposed
    to" -- e.g. a team conceding disproportionately from near-post
    inswingers. Same multi-match/two-contestant requirements as
    :func:`defensive_set_piece_summary`.
    """
    conceded = _conceded_routine_detail(events, set_piece_type, **kwargs)
    if conceded.empty:
        return pd.DataFrame(
            columns=["contestantId", "routine_type", "attempts_faced", "shots_conceded", "goals_conceded", "shot_rate_conceded"]
        )
    out = conceded.groupby(["contestantId", "routine_type"], as_index=False).agg(
        attempts_faced=("eventId", "count"), shots_conceded=("shots", "sum"), goals_conceded=("goals", "sum"),
    )
    out["shot_rate_conceded"] = (out["shots_conceded"] / out["attempts_faced"]).round(3)
    return out.sort_values(["contestantId", "attempts_faced"], ascending=[True, False]).reset_index(drop=True)


def defensive_zone_summary(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    """Per-team, per-destination-zone: same as :func:`defensive_routine_summary`
    but grouped by *where* the ball ended up rather than how it got there.
    """
    conceded = _conceded_routine_detail(events, set_piece_type, **kwargs)
    if conceded.empty:
        return pd.DataFrame(
            columns=["contestantId", "destination_zone", "attempts_faced", "shots_conceded", "goals_conceded", "shot_rate_conceded"]
        )
    known = conceded.dropna(subset=["destination_zone"])
    out = known.groupby(["contestantId", "destination_zone"], as_index=False).agg(
        attempts_faced=("eventId", "count"), shots_conceded=("shots", "sum"), goals_conceded=("goals", "sum"),
    )
    out["shot_rate_conceded"] = (out["shots_conceded"] / out["attempts_faced"]).round(3)
    return out.sort_values(["contestantId", "attempts_faced"], ascending=[True, False]).reset_index(drop=True)


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
