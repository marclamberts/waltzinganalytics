"""
What a team concedes most from corners
==========================================

``defensive_routine_summary`` and ``defensive_zone_summary`` flip
``restart_routines``'s attacking-team perspective to the defending side:
which routine types, and which destination zones, is this team's
defending most exposed to. Same per-match, two-contestant requirement as
``defensive_set_piece_summary``.
"""

from pathlib import Path

from wa_setpieces import load_matches
from wa_setpieces.core.defending import defensive_routine_summary, defensive_zone_summary
from wa_setpieces.viz.plots import plot_defensive_routine_bars

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)

# %%
# By routine type:
conceded_routines = defensive_routine_summary(events, "corner")
conceded_routines

# %%
team_id = conceded_routines["contestantId"].iloc[0]
fig, ax = plot_defensive_routine_bars(conceded_routines, team_id=team_id)

# %%
# By destination zone -- *where* the ball ended up, not how it got there:
conceded_zones = defensive_zone_summary(events, "corner")
conceded_zones

# %%
fig, ax = plot_defensive_routine_bars(
    conceded_zones, team_id=team_id, metric="shots_conceded",
    title="Shots conceded by destination zone",
)
