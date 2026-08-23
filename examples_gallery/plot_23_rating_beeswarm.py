"""
Rating spread: beeswarm
==========================

:func:`~wa_setpieces.viz.plots.plot_rating_benchmark` ranks players as
horizontal bars -- great for "who's best," but it can't show whether the
squad is one tight cluster around average or has a real standout and a
long tail. :func:`~wa_setpieces.viz.plots.plot_rating_beeswarm` plots the
same 0-100 rating as one dot per player instead, spread apart just enough
to stay readable, so the *shape* of the distribution is visible at a
glance.

As with every other single-match example in this gallery, ratings here
are z-scored against a sample of six players -- see
:mod:`wa_setpieces.core.rating`'s module docstring on why a real rating
needs a full season/competition behind it, not one match.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.rating import player_rating
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_rating_beeswarm

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
rated = player_rating(match.events, "corner", model, min_deliveries=1, min_shots=1)
rated[["playerName", "contestantId", "rating"]]

# %%
fig, ax = plot_rating_beeswarm(rated, title="Corner rating spread")
