"""wa-setpieces: set-piece metrics (penalties, kick-offs, free kicks,
corners, throw-ins, goal kicks) from Opta / Stats Perform F24 -- and, via
:mod:`wa_setpieces.providers`, StatsBomb -- event data.

Layout:

- :mod:`wa_setpieces.core` -- loading, extraction, metrics, phases,
  retention, xT, added-value and :mod:`~wa_setpieces.core.rating` (no
  extra dependencies; imported eagerly).
- :mod:`wa_setpieces.providers` -- adapters that convert other providers'
  feeds (currently StatsBomb) into the same internal events frame Opta F24
  produces, so everything else works unchanged regardless of source.
- :mod:`wa_setpieces.ml` -- pre-trained shot-value scoring (``ml`` extra).
- :mod:`wa_setpieces.viz` -- mplsoccer/matplotlib plots (``viz`` extra).
- :mod:`wa_setpieces.convert` -- turn raw Opta F24 exports plus a match
  list into the flat corner/delivery table other tools expect.

The names below are the stable public API and are re-exported here so
``from wa_setpieces import load_events`` keeps working regardless of which
submodule they actually live in.
"""

from .core.chains import link_set_piece_shots, set_piece_goal_summary
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
from .core.loader import Match, load_events, load_events_multi
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
from .providers.statsbomb import load_statsbomb_events
from .core.outcomes import OUTCOME_CATEGORIES, delivery_outcomes, outcome_summary
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

__version__ = "0.10.0"

__all__ = [
    "Match",
    "load_events",
    "load_events_multi",
    "load_statsbomb_events",
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
