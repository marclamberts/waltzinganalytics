"""
Set-piece added value
========================

:mod:`wa_setpieces.core.value` blends two things into one number per delivery:
the xT added by the delivery itself, and -- if it produced a shot, whether
straight off the ball or via a second-phase loose ball -- how good a
chance that shot was. ``added_value = delivery_xt_added + shot_value``.

The shot link comes from Opta's own assist-chain qualifier
(:func:`wa_setpieces.core.chains.link_set_piece_shots`), scoped to the shooting
team's own event stream -- ``eventId`` is only unique *within one team's
event stream* in F24 (both teams number their events 1, 2, 3, ...
independently), so resolving it without that scoping can silently
attribute a shot to the wrong team's delivery.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.value import set_piece_added_value, set_piece_value_summary
from wa_setpieces.viz.plots import plot_xt_added_bars
from wa_setpieces.core.xt import XTModel

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
# Per-delivery breakdown for free kicks:
set_piece_added_value(match.events, "free_kick", model)

# %%
# Ranked, as a diverging bar chart (green = created value, red = cost it):
free_kick_value = set_piece_added_value(match.events, "free_kick", model)
fig, ax = plot_xt_added_bars(
    free_kick_value, value_col="added_value", title="Free-kick added value"
)

# %%
# Rolled up per team:
set_piece_value_summary(match.events, "corner", model)
