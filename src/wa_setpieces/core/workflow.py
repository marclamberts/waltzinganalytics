"""One-call pipeline: extraction through rating, for one set-piece type.

This package's usual workflow is a chain -- extract the set piece, count
attempts by team/player, detect second phases and retention, blend in
delivery/shot value, roll it into a report, then benchmark a rating from
that report. :func:`run_workflow` runs that whole chain in one call and
hands back every table in a single :class:`SetPieceWorkflow`, for when you
want the full pipeline without wiring five function calls together
yourself. It computes nothing new -- every field is exactly what the
underlying function (:mod:`wa_setpieces.core.metrics`,
:mod:`wa_setpieces.core.phases`, :mod:`wa_setpieces.core.retention`,
:mod:`wa_setpieces.core.value`, :mod:`wa_setpieces.core.report`,
:mod:`wa_setpieces.core.rating`) already returns. Reach for those directly
when you only need one piece, want different parameters per step, or are
combining several matches (see :func:`~wa_setpieces.load_events_multi`'s
docstring on what is and isn't safe to concatenate first).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import constants as c
from .metrics import delivery_locations, player_set_piece_counts, set_piece_summary, team_set_piece_counts
from .phases import second_phases as _second_phases
from .rating import player_rating as _player_rating
from .rating import team_rating as _team_rating
from .report import set_piece_report
from .retention import retention_detail
from .value import set_piece_added_value
from .xt import XTModel

_PHASE_TYPES = ("corner", "free_kick")


@dataclass
class SetPieceWorkflow:
    """Every table :func:`run_workflow` produces for one set-piece type, in
    pipeline order. Fields that don't apply to ``set_piece_type`` (e.g.
    ``deliveries`` for a penalty, or anything needing ``model`` when none
    was passed) are ``None`` rather than an empty DataFrame, so a truthy
    check tells you whether that step ran at all.
    """

    set_piece_type: str
    summary: pd.DataFrame
    team_counts: pd.DataFrame
    player_counts: pd.DataFrame
    deliveries: pd.DataFrame | None
    second_phases: pd.DataFrame | None
    retention: pd.DataFrame | None
    added_value: pd.DataFrame | None
    report: pd.DataFrame
    team_rating: pd.DataFrame
    player_rating: pd.DataFrame | None


def run_workflow(
    events: pd.DataFrame,
    set_piece_type: str,
    model: XTModel | None = None,
    retention_window_seconds: float = 8.0,
    min_deliveries: int = 3,
    min_shots: int = 1,
) -> SetPieceWorkflow:
    """Run this package's full pipeline for one set-piece type in one call.

    Args:
        set_piece_type: any of ``constants.SET_PIECE_TYPES``.
        model: optional fitted :class:`~wa_setpieces.core.xt.XTModel`.
            Unlocks ``added_value``, ``report``'s added-value columns and
            ``player_rating`` -- all ``None``/unavailable without it. Only
            meaningful for ``"corner"``/``"free_kick"`` either way (see
            :func:`~wa_setpieces.core.value.set_piece_added_value`).
        retention_window_seconds: passed through to
            :func:`~wa_setpieces.core.retention.retention_detail` and the
            report's retention rate.
        min_deliveries, min_shots: passed through to
            :func:`~wa_setpieces.core.rating.player_rating` -- see that
            function's docstring on why too small a sample is excluded
            rather than rated on noise.

    Returns:
        A :class:`SetPieceWorkflow`. Remember ratings are only as
        meaningful as the sample in ``events`` -- run this over a full
        season/competition for the rating fields to mean anything (see
        :mod:`wa_setpieces.core.rating`'s module docstring).
    """
    if set_piece_type not in c.SET_PIECE_TYPES:
        raise ValueError(f"set_piece_type must be one of {c.SET_PIECE_TYPES}, got {set_piece_type!r}")

    summary = set_piece_summary(events)
    summary = summary.loc[summary["set_piece_type"] == set_piece_type].reset_index(drop=True)
    team_counts = team_set_piece_counts(events)
    team_counts = team_counts.loc[team_counts["set_piece_type"] == set_piece_type].reset_index(drop=True)
    player_counts = player_set_piece_counts(events)
    player_counts = player_counts.loc[player_counts["set_piece_type"] == set_piece_type].reset_index(drop=True)

    deliveries = delivery_locations(events, set_piece_type) if set_piece_type in c.SET_PIECE_QUALIFIERS else None
    phases = _second_phases(events, set_piece_type) if set_piece_type in _PHASE_TYPES else None
    retention = retention_detail(events, set_piece_type, window_seconds=retention_window_seconds) \
        if set_piece_type != "penalty" else None
    added_value = set_piece_added_value(events, set_piece_type, model) \
        if model is not None and set_piece_type in _PHASE_TYPES else None

    report = set_piece_report(
        events, set_piece_type, model=model, retention_window_seconds=retention_window_seconds
    )
    team_rated = _team_rating(report)
    player_rated = _player_rating(
        events, set_piece_type, model, min_deliveries=min_deliveries, min_shots=min_shots
    ) if model is not None and set_piece_type in _PHASE_TYPES else None

    return SetPieceWorkflow(
        set_piece_type=set_piece_type,
        summary=summary,
        team_counts=team_counts,
        player_counts=player_counts,
        deliveries=deliveries,
        second_phases=phases,
        retention=retention,
        added_value=added_value,
        report=report,
        team_rating=team_rated,
        player_rating=player_rated,
    )
