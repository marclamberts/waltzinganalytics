"""One-stop team-level report per set-piece type.

:func:`set_piece_report` merges the pieces that otherwise live in separate
modules -- attempts/success rate (:mod:`wa_setpieces.core.metrics`), second-phase
rate (:mod:`wa_setpieces.core.phases`, corners/free-kicks only), retention
(:mod:`wa_setpieces.core.retention`), and added value (:mod:`wa_setpieces.core.value`,
if you pass a fitted :class:`~wa_setpieces.XTModel`) -- into one table, so
"how are we doing at corners" is one function call instead of five.
"""

from __future__ import annotations

import pandas as pd

from .metrics import team_set_piece_counts
from .retention import retention_rate as _retention_rate

_PHASE_TYPES = ("corner", "free_kick")


def set_piece_report(
    events: pd.DataFrame,
    set_piece_type: str,
    model=None,
    retention_window_seconds: float = 8.0,
) -> pd.DataFrame:
    """Per-team results for one set-piece type: attempts, success rate,
    second-phase rate (corners/free-kicks only), retention rate, and --
    if ``model`` is given -- added value and goals.

    Args:
        set_piece_type: any of ``constants.SET_PIECE_TYPES``.
        model: optional fitted :class:`~wa_setpieces.XTModel`. When given,
            adds ``total_added_value``, ``avg_added_value`` and ``goals``
            columns (see :mod:`wa_setpieces.core.value`); only valid for
            ``"corner"`` and ``"free_kick"`` (the pass-based types with a
            delivery end location).

    Returns:
        One row per team.
    """
    counts = team_set_piece_counts(events)
    out = counts[counts["set_piece_type"] == set_piece_type].drop(columns="set_piece_type")
    out = out.reset_index(drop=True)

    if set_piece_type in _PHASE_TYPES:
        from .phases import second_phase_summary

        phases = second_phase_summary(events, set_piece_type)
        phases = phases.drop(columns="deliveries", errors="ignore")
        out = out.merge(phases, on="contestantId", how="left")
        out["second_phases"] = out["second_phases"].fillna(0).astype(int)
        out["second_phase_goals"] = out["second_phase_goals"].fillna(0).astype(int)
        out["second_phase_rate"] = (out["second_phases"] / out["attempts"]).round(3)

    if set_piece_type != "penalty":
        ret = _retention_rate(events, set_piece_type, window_seconds=retention_window_seconds)
        ret = ret[["contestantId", "retention_rate"]]
        out = out.merge(ret, on="contestantId", how="left")

    if model is not None:
        if set_piece_type not in _PHASE_TYPES:
            raise ValueError(
                f"added value needs a delivery end location, only available for "
                f"{_PHASE_TYPES}, not {set_piece_type!r}"
            )
        from .value import set_piece_value_summary

        value = set_piece_value_summary(events, set_piece_type, model)
        value = value.drop(columns="deliveries", errors="ignore")
        out = out.merge(value, on="contestantId", how="left")

    return out


def corner_report(events: pd.DataFrame, model=None) -> pd.DataFrame:
    """:func:`set_piece_report` for corners."""
    return set_piece_report(events, "corner", model=model)


def free_kick_report(events: pd.DataFrame, model=None) -> pd.DataFrame:
    """:func:`set_piece_report` for free kicks."""
    return set_piece_report(events, "free_kick", model=model)
