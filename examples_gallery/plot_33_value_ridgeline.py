"""
Value distribution: ridgeline
=================================

A joyplot of per-delivery added value: one smooth density curve per
set-piece type instead of :func:`~wa_setpieces.viz.plots.plot_value_distribution`'s
violins. A KDE curve makes a multi-modal shape (two distinct clusters
of outcomes, not just one messy spread) easier to spot than a violin's
mirrored outline does -- at the cost of needing more data to trust: each
type needs at least 3 deliveries with non-identical values, or it's
silently left out.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_value_ridgeline

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
fig, ax = plot_value_ridgeline(match.events, model, title="Added value distribution shape")
