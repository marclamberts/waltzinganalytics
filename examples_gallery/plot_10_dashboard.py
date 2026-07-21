"""
Set-piece report card
========================

The "hero" figure: one team's corner delivery map, end-zone heatmap, and
attempts/success-rate comparison against their opponent, combined into a
single shareable image with :func:`~wa_setpieces.viz.plot_dashboard`.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_events
from wa_setpieces.viz.plots import plot_dashboard

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
corners = delivery_locations(match.events, "corner")
team_id = corners["contestantId"].value_counts().idxmax()

# %%
fig = plot_dashboard(match.events, team_id, set_piece_type="corner")
