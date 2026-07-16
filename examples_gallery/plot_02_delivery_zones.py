"""
Where deliveries end up: zone heatmaps
=========================================

:mod:`opta_setpieces.zones` splits the pitch into thirds, wide/half-space/
central channels, or a configurable zone grid. Here we grid where corner
and free-kick deliveries *land* (their end location), which is far more
informative than where they start (always the corner arc / free-kick spot).
"""

from pathlib import Path

import pandas as pd

from opta_setpieces import delivery_locations, load_events
from opta_setpieces.viz import plot_zone_heatmap
from opta_setpieces.zones import add_channels

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Corner end-locations, gridded into a 6x3 zone heatmap:
corners = delivery_locations(match.events, "corner")
fig, ax = plot_zone_heatmap(
    corners, x_col="end_x", y_col="end_y", title="Corner delivery end zones"
)

# %%
# Free kicks tend to be played from deeper -- compare the end-zone spread:
free_kicks = delivery_locations(match.events, "free_kick")
fig, ax = plot_zone_heatmap(
    free_kicks, x_col="end_x", y_col="end_y", title="Free-kick delivery end zones", cmap="Blues"
)

# %%
# Zones aren't just for pitch heatmaps -- ``add_channels`` works on any
# DataFrame with x/y columns, e.g. to see which width channel throw-ins are
# taken from:
throw_ins = delivery_locations(match.events, "throw_in")
throw_ins = add_channels(throw_ins, n=5)
throw_ins["channel"].value_counts()
