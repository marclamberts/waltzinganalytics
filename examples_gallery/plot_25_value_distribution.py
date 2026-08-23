"""
Value distribution: violins
==============================

Every other value chart in this gallery plots a total or an average.
This one plots the *spread*: a violin per set-piece type of
per-delivery added value. A wide violin is a type that's either
brilliant or costly depending on the delivery -- high variance, worth
digging into which deliveries drove which tail. A tight one is
consistently middling either way.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_value_distribution

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
fig, ax = plot_value_distribution(match.events, model, title="Added value distribution")
