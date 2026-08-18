"""Video-clip timestamp windows for tagged set-piece deliveries."""

from __future__ import annotations

import pandas as pd

from . import constants as c
from .filters import tag_set_pieces


def delivery_clip_windows(
    events: pd.DataFrame,
    set_piece_type: str,
    *,
    pre_seconds: float = 5.0,
    post_seconds: float = 15.0,
) -> pd.DataFrame:
    """Clip in/out windows for every delivery of one set-piece type, ready
    to hand off to a video-clipping tool.

    Opta's ``timeMin``/``timeSec`` already run cumulatively across periods
    within a match (period 2 continues from ~45, it doesn't reset to 0 --
    see :mod:`wa_setpieces.core.loader`), so ``event_seconds`` is already a
    single increasing match-clock value; the clip window is just that +/-
    ``pre_seconds``/``post_seconds`` (start clamped to not go negative).
    These are match-clock seconds, not video-file timestamps -- align them
    to your own footage's period/kickoff boundaries before cutting.

    Args:
        set_piece_type: any of ``constants.SET_PIECE_TYPES``.
        pre_seconds: seconds of context to include before the delivery.
        post_seconds: seconds of context to include after the delivery.

    Returns:
        One row per delivery: ``eventId``, ``contestantId``, ``playerId``,
        ``playerName``, ``periodId``, ``timeMin``, ``timeSec``,
        ``event_seconds``, ``clip_start_seconds``, ``clip_end_seconds``,
        plus ``matchId`` when present in ``events``.
    """
    if set_piece_type not in c.SET_PIECE_TYPES:
        raise ValueError(f"set_piece_type must be one of {c.SET_PIECE_TYPES}, got {set_piece_type!r}")
    if pre_seconds < 0 or post_seconds < 0:
        raise ValueError("pre_seconds and post_seconds must be non-negative")

    tagged = tag_set_pieces(events)
    deliveries = tagged.loc[tagged["set_piece_type"] == set_piece_type].copy()
    event_seconds = (
        pd.to_numeric(deliveries["timeMin"], errors="coerce") * 60.0
        + pd.to_numeric(deliveries["timeSec"], errors="coerce")
    )
    deliveries["event_seconds"] = event_seconds
    deliveries["clip_start_seconds"] = (event_seconds - pre_seconds).clip(lower=0)
    deliveries["clip_end_seconds"] = event_seconds + post_seconds

    cols = [
        "eventId", "contestantId", "playerId", "playerName", "periodId",
        "timeMin", "timeSec", "event_seconds", "clip_start_seconds", "clip_end_seconds",
    ]
    if "matchId" in deliveries.columns:
        cols = ["matchId", *cols]
    return deliveries[cols].reset_index(drop=True)
