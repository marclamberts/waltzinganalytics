"""wa-setpieces: set-piece metrics (penalties, kick-offs, free kicks,
corners, throw-ins, goal kicks) from Opta / Stats Perform, StatsBomb, or
IMPECT event data.

Layout:

- :mod:`wa_setpieces.core` -- loading, extraction, metrics, phases,
  retention, xT, added-value and :mod:`~wa_setpieces.core.rating` (no
  extra dependencies; imported eagerly).
- :mod:`wa_setpieces.providers` -- per-provider converters (StatsBomb,
  IMPECT) into the same internal events frame Opta produces, so
  everything else works unchanged regardless of source. Prefer
  :func:`load_matches` over importing from here directly.
- :mod:`wa_setpieces.ml` -- pre-trained shot-value scoring (``ml`` extra).
- :mod:`wa_setpieces.viz` -- mplsoccer/matplotlib plots (``viz`` extra).
- :mod:`wa_setpieces.convert` -- turn raw Opta exports plus a match
  list into the flat corner/delivery table other tools expect.

:func:`load_matches` is the one loading entry point for any provider and
either a single match file or a whole folder of them (a season) -- pass
``provider="opta"`` (default), ``"statsbomb"`` or ``"impect"``. Use
:func:`load_events` instead only when you specifically want one Opta
match's raw ``matchDetails`` block alongside its events (the
:class:`~wa_setpieces.core.loader.Match` object), rather than a
combined, ``matchId``-tagged events frame.

The names below are the stable public API and are re-exported here so
``from wa_setpieces import load_events`` keeps working regardless of which
submodule they actually live in.
"""

from .core.chains import link_set_piece_shots, set_piece_goal_summary
from .core.clips import delivery_clip_windows
from .core.filters import (
    extract_all,
    extract_corners,
    extract_free_kicks,
    extract_goal_kicks,
    extract_kick_offs,
    extract_penalties,
    extract_throw_ins,
    tag_set_pieces,
)
from .core.loader import Match, load_events, load_events_multi, load_matches
from .core.schema import EventCapabilities, EventSchemaError, event_capabilities, validate_events
from .core.season import SeasonDataset
from .core.defending import (
    defensive_rating,
    defensive_routine_summary,
    defensive_set_piece_summary,
    defensive_zone_summary,
)
from .core.attribution import first_contact_detail, first_contact_summary
from .core.penalties import penalty_placement_detail, penalty_taker_summary
from .core.routines import (
    RoutineAnalysis,
    all_routine_summaries,
    analyze_routines,
    cluster_routines,
    cluster_summary,
    long_throw_second_phases,
    long_throw_taker_summary,
    restart_routines,
    routine_summary,
    routine_taker_profiles,
    routine_target_matrix,
    routine_team_profiles,
)
from .reporting import (
    corner_report_html,
    opponent_scouting_report_html,
    render_html_report,
    save_table,
    save_tables,
    write_html_report,
)
from .core.metrics import (
    delivery_locations,
    player_set_piece_counts,
    set_piece_summary,
    team_set_piece_counts,
)
from .core.phases import (
    PhaseResult,
    classify_phase,
    second_phase_summary,
    second_phases,
)
from .providers.impect import load_impect_events
from .providers.statsbomb import load_statsbomb_events
from .core.outcomes import OUTCOME_CATEGORIES, aerial_duel_summary, delivery_outcomes, outcome_summary
from .core.rating import (
    player_delivery_rating,
    player_finishing_rating,
    player_rating,
    team_rating,
)
from .core.report import corner_report, free_kick_report, set_piece_report
from .core.retention import retention_detail, retention_rate
from .core.workflow import SetPieceWorkflow, run_workflow
from .ml.shot_value import ShotValueModels, build_shot_features, shot_value
from .core.value import set_piece_added_value, set_piece_value_summary
from .core.xt import XTModel, set_piece_delivery_xt, set_piece_xt_summary
from .core.zones import (
    add_channels,
    add_thirds,
    add_zone_grid,
    to_reference_frame,
    zone_counts,
    zone_id,
)

try:
    # Single source of truth is pyproject.toml's [project] version, read
    # from the installed package's own metadata -- a hardcoded string
    # here silently drifted out of sync with real releases before (found
    # reading "0.18.3" while pyproject.toml was already at 0.29.1).
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("wa-setpieces")
except Exception:  # pragma: no cover -- editable/uninstalled checkout
    __version__ = "0.0.0+unknown"

__all__ = [
    "Match",
    "load_events",
    "load_events_multi",
    "load_matches",
    "load_statsbomb_events",
    "load_impect_events",
    "EventCapabilities", "EventSchemaError", "event_capabilities", "validate_events",
    "SeasonDataset", "defensive_set_piece_summary", "defensive_rating",
    "defensive_routine_summary", "defensive_zone_summary",
    "first_contact_detail", "first_contact_summary",
    "penalty_placement_detail", "penalty_taker_summary",
    "restart_routines", "routine_summary", "all_routine_summaries",
    "RoutineAnalysis", "analyze_routines", "routine_team_profiles",
    "routine_taker_profiles", "routine_target_matrix",
    "cluster_routines", "cluster_summary",
    "long_throw_taker_summary", "long_throw_second_phases",
    "delivery_clip_windows",
    "render_html_report", "write_html_report", "corner_report_html",
    "opponent_scouting_report_html",
    "save_table", "save_tables",
    "extract_all",
    "extract_corners",
    "extract_free_kicks",
    "extract_goal_kicks",
    "extract_kick_offs",
    "extract_penalties",
    "extract_throw_ins",
    "tag_set_pieces",
    "link_set_piece_shots",
    "set_piece_goal_summary",
    "team_set_piece_counts",
    "player_set_piece_counts",
    "delivery_locations",
    "set_piece_summary",
    "PhaseResult",
    "classify_phase",
    "second_phases",
    "second_phase_summary",
    "retention_detail",
    "retention_rate",
    "XTModel",
    "set_piece_delivery_xt",
    "set_piece_xt_summary",
    "set_piece_added_value",
    "set_piece_value_summary",
    "set_piece_report",
    "corner_report",
    "free_kick_report",
    "OUTCOME_CATEGORIES",
    "delivery_outcomes",
    "outcome_summary",
    "aerial_duel_summary",
    "team_rating",
    "player_rating",
    "player_delivery_rating",
    "player_finishing_rating",
    "SetPieceWorkflow",
    "run_workflow",
    "ShotValueModels",
    "build_shot_features",
    "shot_value",
    "add_thirds",
    "add_channels",
    "add_zone_grid",
    "to_reference_frame",
    "zone_id",
    "zone_counts",
    "__version__",
]
