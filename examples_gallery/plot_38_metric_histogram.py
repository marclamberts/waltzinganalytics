"""
Delivery distance: histogram
================================

A classic binned histogram of delivery distance (corners and free
kicks combined) -- the simplest possible answer to "what's the
distribution of this number," with no smoothing assumption baked in the
way :func:`~wa_setpieces.viz.plots.plot_value_distribution`'s violins
and :func:`~wa_setpieces.viz.plots.plot_value_ridgeline`'s KDE curves
both have. Works on any continuous metric, not just distance -- hand it
``added_value``, time-to-first-contact, whatever's on hand.
"""

from pathlib import Path

import pandas as pd

from wa_setpieces import delivery_locations, load_events
from wa_setpieces.viz.plots import plot_metric_histogram

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
corners = delivery_locations(match.events, "corner")
free_kicks = delivery_locations(match.events, "free_kick")
combined = pd.concat([corners, free_kicks])
distance = ((combined["end_x"] - combined["x"]) ** 2 + (combined["end_y"] - combined["y"]) ** 2) ** 0.5

# %%
fig, ax = plot_metric_histogram(distance, value_label="delivery distance", title="Delivery distance distribution")
