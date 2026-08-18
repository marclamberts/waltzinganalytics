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
from .defending import defensive_set_piece_summary
from .defending import defensive_routine_summary as _defensive_routine_summary
from .defending import defensive_zone_summary as _defensive_zone_summary
from .attribution import first_contact_detail
from .routines import analyze_routines, cluster_routines
from .routines import long_throw_second_phases as _long_throw_second_phases
from .routines import long_throw_taker_summary as _long_throw_taker_summary
from .outcomes import aerial_duel_summary as _aerial_duel_summary
from .penalties import penalty_placement_detail as _penalty_placement_detail
from .penalties import penalty_taker_summary as _penalty_taker_summary

_PHASE_TYPES = ("corner", "free_kick")


@dataclass
class SetPieceWorkflow:
    """Every table :func:`run_workflow` produces for one set-piece type, in
    pipeline order. Fields that don't apply to ``set_piece_type`` (e.g.
    ``deliveries`` for a penalty, or anything needing ``model`` when none
    was passed), or that need an optional extra that isn't installed
    (``routine_clusters`` needs the ``ml`` extra's scikit-learn), are
    ``None`` rather than an empty DataFrame, so a truthy check tells you
    whether that step ran at all.
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
    defensive_summary: pd.DataFrame
    defensive_routine_summary: pd.DataFrame
    defensive_zone_summary: pd.DataFrame
    first_contacts: pd.DataFrame | None
    routines: pd.DataFrame
    routine_summary: pd.DataFrame
    routine_team_profiles: pd.DataFrame
    routine_taker_profiles: pd.DataFrame
    routine_target_matrix: pd.DataFrame
    routine_clusters: pd.DataFrame | None
    aerial_duel_team_summary: pd.DataFrame | None
    aerial_duel_player_summary: pd.DataFrame | None
    penalty_placement: pd.DataFrame | None
    penalty_taker_summary: pd.DataFrame | None
    long_throw_taker_summary: pd.DataFrame | None
    long_throw_second_phases: pd.DataFrame | None


def run_workflow(
    events: pd.DataFrame,
    set_piece_type: str,
    model: XTModel | None = None,
    retention_window_seconds: float = 8.0,
    min_deliveries: int = 3,
    min_shots: int = 1,
    n_clusters: int = 5,
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
        n_clusters: passed through to
            :func:`~wa_setpieces.core.routines.cluster_routines` for
            ``routine_clusters``.

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
        events, set_piece_type,
        model=model if set_piece_type in _PHASE_TYPES else None,
        retention_window_seconds=retention_window_seconds,
    )
    team_rated = _team_rating(report)
    player_rated = _player_rating(
        events, set_piece_type, model, min_deliveries=min_deliveries, min_shots=min_shots
    ) if model is not None and set_piece_type in _PHASE_TYPES else None
    defending = defensive_set_piece_summary(events)
    defending = defending.loc[defending["set_piece_type"] == set_piece_type].reset_index(drop=True)
    conceded_routines = _defensive_routine_summary(
        events, set_piece_type, retention_window_seconds=retention_window_seconds
    )
    conceded_zones = _defensive_zone_summary(
        events, set_piece_type, retention_window_seconds=retention_window_seconds
    )
    contacts = first_contact_detail(events, set_piece_type) if set_piece_type in c.SET_PIECE_QUALIFIERS else None
    routine_analysis = analyze_routines(
        events, set_piece_type, min_taker_attempts=min_deliveries,
        retention_window_seconds=retention_window_seconds,
    )
    try:
        clusters = cluster_routines(
            events, set_piece_type, n_clusters=n_clusters,
            retention_window_seconds=retention_window_seconds,
        )
    except ImportError:
        clusters = None

    if set_piece_type in _PHASE_TYPES:
        aerial_team, aerial_player = _aerial_duel_summary(events, set_piece_type)
    else:
        aerial_team, aerial_player = None, None

    if set_piece_type == "penalty":
        placement = _penalty_placement_detail(events)
        taker_summary = _penalty_taker_summary(events)
    else:
        placement, taker_summary = None, None

    if set_piece_type == "throw_in":
        long_throw_takers = _long_throw_taker_summary(events)
        long_throw_phases = _long_throw_second_phases(events)
    else:
        long_throw_takers, long_throw_phases = None, None

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
        defensive_summary=defending,
        defensive_routine_summary=conceded_routines,
        defensive_zone_summary=conceded_zones,
        first_contacts=contacts,
        routines=routine_analysis.detail,
        routine_summary=routine_analysis.summary,
        routine_team_profiles=routine_analysis.team_profiles,
        routine_taker_profiles=routine_analysis.taker_profiles,
        routine_target_matrix=routine_analysis.target_matrix,
        routine_clusters=clusters,
        aerial_duel_team_summary=aerial_team,
        aerial_duel_player_summary=aerial_player,
        penalty_placement=placement,
        penalty_taker_summary=taker_summary,
        long_throw_taker_summary=long_throw_takers,
        long_throw_second_phases=long_throw_phases,
    )
