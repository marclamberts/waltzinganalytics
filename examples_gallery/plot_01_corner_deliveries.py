"""
Corner delivery map
=====================

Where each team's corners were aimed, and whether they found a teammate.
Green arrows are successful deliveries, red are unsuccessful.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_events
from wa_setpieces.viz.plots import plot_delivery_map

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

# %%
# Load the match and pull out every corner's start/end coordinates.
match = load_events(DATA)
corners = delivery_locations(match.events, "corner")
corners.head()

# %%
# One team's corners:
team_id = corners["contestantId"].value_counts().idxmax()
team_corners = corners[corners["contestantId"] == team_id]

fig, ax = plot_delivery_map(team_corners, title=f"Corners — team {team_id[:8]}…")

# %%
# All corners from both teams, on one pitch:
fig, ax = plot_delivery_map(corners, title="All corners, both teams")
