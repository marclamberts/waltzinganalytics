"""
xT added, ranked
===================

A diverging bar chart: which deliveries added the most (or cost the most)
Expected Threat. Positive/negative is a signed quantity, so it gets the
blue/red diverging pair with a gray zero baseline -- not the categorical
team colors, and not the green/red success-status colors used elsewhere.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.viz import plot_xt_added_bars
from wa_setpieces.xt import XTModel, set_piece_delivery_xt

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
free_kick_xt = set_piece_delivery_xt(match.events, "free_kick", model)
fig, ax = plot_xt_added_bars(free_kick_xt, title="xT added — free kicks")

# %%
corner_xt = set_piece_delivery_xt(match.events, "corner", model)
fig, ax = plot_xt_added_bars(corner_xt, title="xT added — corners")
