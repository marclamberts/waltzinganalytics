"""
Value distribution: box plot
================================

Exact quartiles, median, and outlier points per set-piece type --
:func:`~wa_setpieces.viz.plots.plot_value_distribution`'s violins show
the smoothed *shape* of this same data, and
:func:`~wa_setpieces.viz.plots.plot_value_ridgeline`'s KDE curves show
it again a third way. Reach for the box plot when the specific numbers
(median, IQR, which points are outliers) matter more than the overall
shape -- a corner delivery costing -0.019 xT stands out here as a
labeled outlier point, not just a wide tail on a curve.
"""

from pathlib import Path

from wa_setpieces import load_matches
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_value_boxplot

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
model = XTModel.fit(events, x_bins=8, y_bins=6)

# %%
fig, ax = plot_value_boxplot(events, model, title="Added value by set-piece type")
