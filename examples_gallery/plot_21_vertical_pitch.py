"""
Vertical pitch orientation
=============================

Every pitch-based plotting function (a delivery map, a zone heatmap, a
second-phase sequence, an outcome shot map, routine clusters) takes
``vertical: bool = False`` -- draws on :class:`mplsoccer.VerticalPitch`
(goal-at-top) instead of the default :class:`mplsoccer.Pitch`
(goal-at-right) when ``True``. Nothing else about the call changes: both
mplsoccer classes share the same drawing API, so the same
``delivery_locations``/``zone_counts``/... output plugs into either one
unchanged.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_events
from wa_setpieces.viz.plots import plot_delivery_map, plot_zone_heatmap

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
corners = delivery_locations(match.events, "corner")

# %%
# Horizontal (the default):
fig, ax = plot_delivery_map(corners, title="Corner deliveries", subtitle="Horizontal (default)")

# %%
# The same deliveries, vertical:
fig, ax = plot_delivery_map(corners, title="Corner deliveries", subtitle="Vertical", vertical=True)

# %%
# Works the same way for a zone heatmap -- the grid itself rotates with
# the pitch (a 6x3 grid horizontally becomes 3x6 vertically), not just
# the outline:
fig, ax = plot_zone_heatmap(
    corners, x_col="end_x", y_col="end_y",
    title="Corner delivery end zones", subtitle="Vertical", vertical=True,
)
