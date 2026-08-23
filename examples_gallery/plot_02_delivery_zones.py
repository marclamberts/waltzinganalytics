"""
Where deliveries end up: zone scatter and heatmaps
======================================================

:mod:`wa_setpieces.core.zones` splits the pitch into thirds, wide/half-space/
central channels, or a configurable zone grid. Here we look at where corner
and free-kick deliveries *land* (their end location), which is far more
informative than where they start (always the corner arc / free-kick spot)
-- first as individual points, then as a binned grid.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_matches
from wa_setpieces.viz.plots import plot_zone_heatmap, plot_zone_scatter
from wa_setpieces.core.zones import add_channels

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)

# %%
# Every corner's end-location as its own point, colored by outcome and
# shaded by density underneath -- no binning choice deciding how coarse the
# picture is, and success/failure is visible per point, not just an
# aggregate count:
corners = delivery_locations(events, "corner")
fig, ax = plot_zone_scatter(
    corners, x_col="end_x", y_col="end_y", title="Corner delivery landing spots",
)

# %%
# The same idea for free kicks:
free_kicks = delivery_locations(events, "free_kick")
fig, ax = plot_zone_scatter(
    free_kicks, x_col="end_x", y_col="end_y", title="Free-kick delivery landing spots",
)

# %%
# Reach for the binned grid instead when exact per-zone counts are the
# point, not the shape of the pattern:
fig, ax = plot_zone_heatmap(
    corners, x_col="end_x", y_col="end_y", title="Corner delivery end zones",
)

# %%
# Zones aren't just for pitch plots -- ``add_channels`` works on any
# DataFrame with x/y columns, e.g. to see which width channel throw-ins are
# taken from:
throw_ins = delivery_locations(events, "throw_in")
throw_ins = add_channels(throw_ins, n=5)
throw_ins["channel"].value_counts()
