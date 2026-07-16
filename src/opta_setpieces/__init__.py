"""opta-setpieces: set-piece metrics (penalties, kick-offs, free kicks,
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
from .loader import Match, load_events
from .metrics import (
    delivery_locations,
    player_set_piece_counts,
    set_piece_summary,
    team_set_piece_counts,
)

__version__ = "0.1.0"

__all__ = [
    "Match",
    "load_events",
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
    "__version__",
]
