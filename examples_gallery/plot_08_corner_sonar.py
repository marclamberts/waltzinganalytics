"""
Corner sonar
==============

A polar view of corner deliveries: angle is the direction the ball
travelled from the corner spot, radius is how far. Clusters reveal a
team's default delivery pattern (near post, far post, short) at a glance
in a way an on-pitch arrow map doesn't.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_events
from wa_setpieces.viz import plot_corner_sonar

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
corners = delivery_locations(match.events, "corner")

# %%
fig, ax = plot_corner_sonar(corners, title="All corners, both teams")

# %%
team_id = corners["contestantId"].value_counts().idxmax()
team_corners = corners[corners["contestantId"] == team_id]
fig, ax = plot_corner_sonar(team_corners, title=f"Corners — team {team_id[:8]}…")
