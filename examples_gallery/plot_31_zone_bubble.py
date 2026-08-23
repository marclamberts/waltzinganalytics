"""
End zones: bubbles
=====================

Zone counts as size-encoded bubbles on the pitch, instead of
:func:`~wa_setpieces.viz.plots.plot_zone_heatmap`'s color-encoded grid.
Size is a more intuitive read of "how many" than a color ramp -- no
legend needed to compare two bubbles' areas -- at the cost of precision
for zones with close counts, where a heatmap's exact color-to-value
mapping does better. Each bubble carries its own count label, so that
trade-off costs nothing here.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_matches
from wa_setpieces.viz.plots import plot_zone_bubble

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
corners = delivery_locations(events, "corner")

# %%
fig, ax = plot_zone_bubble(corners, x_col="end_x", y_col="end_y", title="Corner end-zone bubbles")
