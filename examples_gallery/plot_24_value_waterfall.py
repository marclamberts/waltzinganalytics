"""
Value waterfall
==================

One team's total set-piece added value, decomposed by restart type as a
waterfall: each type's own bar floats from wherever the running total
already sat, and a final bar shows where they land. Green is a type that
added value, red is a type that cost it -- a team can be genuinely bad
at one restart type and good at another, and a single combined number
would hide that.

A different question than :func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow`'s
step chart: that one shows *when* value accumulated over the match, this
shows *which restart type* it came from.
"""

from pathlib import Path

from wa_setpieces import load_matches, set_piece_summary
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_value_waterfall

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
model = XTModel.fit(events, x_bins=8, y_bins=6)
team_id = set_piece_summary(events)["contestantId"].iloc[0]

# %%
fig, ax = plot_value_waterfall(events, team_id, model, title="Added value by restart type")
