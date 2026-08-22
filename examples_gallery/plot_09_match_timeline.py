"""
Match timeline and value flow
================================

Two ways of looking at *when* things happened, not just how many. First,
every set piece in the match on one shared timeline -- one row per restart
type, one dot per delivery, positioned by match minute. Good for spotting
patterns like a team leaning on throw-ins early or corners piling up late.

Second, cumulative set-piece added value over the match -- a step chart
showing when each team's set-piece threat was actually created, not just
the final total.
"""

from pathlib import Path

from wa_setpieces import load_events, XTModel
from wa_setpieces.viz.plots import plot_match_timeline, plot_set_piece_value_flow

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
fig, ax = plot_match_timeline(match.events)

# %%
# Fitting on one match, as below, is illustrative only -- see
# :doc:`../value_models` on why a real xT model needs a season's worth of
# data. Corners and free kicks are the only two types with a value model,
# so they're what gets combined here by default.
model = XTModel.fit(match.events)
fig, ax = plot_set_piece_value_flow(match.events, model)
