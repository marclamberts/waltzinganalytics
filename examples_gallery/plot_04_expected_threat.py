"""
Expected Threat (xT) for corners and free kicks
==================================================

:class:`wa_setpieces.XTModel` implements Karun Singh's grid-based xT
method: fit a grid of zone values from data, then value any pass as
``xT[end_zone] - xT[start_zone]``.

.. important::
   The grid below is fit on a **single match**, purely to demonstrate the
   mechanism -- it is far too little data for a trustworthy grid. Fit on a
   full season (concatenate many matches' events) for real analysis, then
   reuse it with :meth:`~wa_setpieces.XTModel.to_csv` /
   :meth:`~wa_setpieces.XTModel.from_csv`.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.viz.plots import plot_xt_grid
from wa_setpieces.core.xt import XTModel, set_piece_delivery_xt, set_piece_xt_summary

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Fit the grid and look at it directly -- value should climb steadily
# towards the opponent's goal (x=100 in each event's own attacking frame).
model = XTModel.fit(match.events, x_bins=8, y_bins=6)
fig, ax = plot_xt_grid(model)

# %%
# xT added by every corner delivery (NaN where the corner didn't find a
# teammate -- there's no reliable end location to value):
set_piece_delivery_xt(match.events, "corner", model)[
    ["eventId", "contestantId", "outcome", "xt_start", "xt_end", "xt_added"]
]

# %%
# Rolled up per team, for both corners and free kicks:
set_piece_xt_summary(match.events, "corner", model)

# %%
set_piece_xt_summary(match.events, "free_kick", model)
