"""Extract set-piece events (penalties, kick-offs, free kicks, corners,
throw-ins, goal kicks) from a parsed Opta F24 events DataFrame.
"""

from __future__ import annotations

import pandas as pd

from . import constants as c


def _qualifier_present(events: pd.DataFrame, qualifier_id: int) -> pd.Series:
    col = f"q_{qualifier_id}"
    if col not in events.columns:
        return pd.Series(False, index=events.index)
    return events[col].notna()


def extract_corners(events: pd.DataFrame) -> pd.DataFrame:
    """Corner kicks: passes tagged with the "Corner taken" qualifier (6)."""
    mask = (events["typeId"] == c.TYPE_PASS) & _qualifier_present(
        events, c.QUALIFIER_CORNER_TAKEN
    )
    return events.loc[mask].copy()


def extract_free_kicks(events: pd.DataFrame) -> pd.DataFrame:
    """Free kicks: passes tagged with the "Free kick taken" qualifier (5).

    Note this includes indirect and direct free kicks alike. Corners are
    technically a subset of free-kick restarts in the laws of the game but
    Opta tags them with a distinct qualifier, so :func:`extract_corners`
    events are excluded here to keep the six categories mutually exclusive.
    """
    mask = (
        (events["typeId"] == c.TYPE_PASS)
        & _qualifier_present(events, c.QUALIFIER_FREE_KICK_TAKEN)
        & ~_qualifier_present(events, c.QUALIFIER_CORNER_TAKEN)
    )
    return events.loc[mask].copy()


def extract_throw_ins(events: pd.DataFrame) -> pd.DataFrame:
    """Throw-ins: passes tagged with the "Throw-in" qualifier (107)."""
    mask = (events["typeId"] == c.TYPE_PASS) & _qualifier_present(
        events, c.QUALIFIER_THROW_IN
    )
    return events.loc[mask].copy()


def extract_goal_kicks(events: pd.DataFrame) -> pd.DataFrame:
    """Goal kicks: passes tagged with the "Goal kick" qualifier (124)."""
    mask = (events["typeId"] == c.TYPE_PASS) & _qualifier_present(
        events, c.QUALIFIER_GOAL_KICK
    )
    return events.loc[mask].copy()


def extract_kick_offs(events: pd.DataFrame) -> pd.DataFrame:
    """Kick-offs: passes tagged with the "Kick off" qualifier (279).

    Fires at kick-off proper and after every goal conceded.
    """
    mask = (events["typeId"] == c.TYPE_PASS) & _qualifier_present(
        events, c.QUALIFIER_KICK_OFF
    )
    return events.loc[mask].copy()


def extract_penalties(events: pd.DataFrame) -> pd.DataFrame:
    """Penalty kicks: shot events (miss/post/saved/goal) tagged "Penalty" (9).

    Unlike the other set pieces, penalties are not passes -- they are shots
    at goal, so they live on :data:`constants.SHOT_TYPE_IDS` rather than
    ``typeId == 1``.
    """
    mask = events["typeId"].isin(c.SHOT_TYPE_IDS) & _qualifier_present(
        events, c.QUALIFIER_PENALTY
    )
    return events.loc[mask].copy()


_EXTRACTORS = {
    "penalty": extract_penalties,
    "kick_off": extract_kick_offs,
    "free_kick": extract_free_kicks,
    "corner": extract_corners,
    "throw_in": extract_throw_ins,
    "goal_kick": extract_goal_kicks,
}


def extract_all(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Run every extractor, keyed by set-piece type name.

    Returns:
        Dict mapping each of ``constants.SET_PIECE_TYPES`` to its DataFrame
        of matching events.
    """
    return {name: fn(events) for name, fn in _EXTRACTORS.items()}


def tag_set_pieces(events: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``events`` with a ``set_piece_type`` column.

    Rows that are not part of any set piece get ``None``. Rows matching more
    than one category (which should not normally happen) keep the first
    match in ``constants.SET_PIECE_TYPES`` order.
    """
    out = events.copy()
    out["set_piece_type"] = None
    for name in c.SET_PIECE_TYPES:
        idx = _EXTRACTORS[name](events).index
        still_untagged = out.loc[idx, "set_piece_type"].isna()
        out.loc[idx[still_untagged], "set_piece_type"] = name
    return out
