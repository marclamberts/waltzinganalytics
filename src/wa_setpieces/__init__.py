"""wa-setpieces: set-piece metrics (penalties, kick-offs, free kicks,
corners, throw-ins, goal kicks) from Opta / Stats Perform F24 event data.
"""

from .chains import link_set_piece_shots, set_piece_goal_summary
from .filters import (
    extract_all,
    extract_corners,
    extract_free_kicks,
    extract_goal_kicks,
    extract_kick_offs,
    extract_penalties,
    extract_throw_ins,
    tag_set_pieces,
)
from .loader import Match, load_events, load_events_multi
from .metrics import (
    delivery_locations,
    player_set_piece_counts,
    set_piece_summary,
    team_set_piece_counts,
)
from .phases import (
    PhaseResult,
    classify_phase,
    second_phase_summary,
    second_phases,
)
from .report import corner_report, free_kick_report, set_piece_report
from .retention import retention_detail, retention_rate
from .value import set_piece_added_value, set_piece_value_summary
from .xt import XTModel, set_piece_delivery_xt, set_piece_xt_summary
from .zones import (
    add_channels,
    add_thirds,
    add_zone_grid,
    to_reference_frame,
    zone_counts,
    zone_id,
)

__version__ = "0.5.1"

__all__ = [
    "Match",
    "load_events",
    "load_events_multi",
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
    "add_thirds",
    "add_channels",
    "add_zone_grid",
    "to_reference_frame",
    "zone_id",
    "zone_counts",
    "__version__",
]
