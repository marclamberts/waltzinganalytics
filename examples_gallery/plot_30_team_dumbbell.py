"""
Team comparison: dumbbell
============================

An alternative to :func:`~wa_setpieces.viz.plots.plot_team_comparison`'s
grouped bars for exactly two teams: one connected pair of dots per
set-piece type instead of two bars sharing a baseline. The connecting
line makes the *gap* between teams the thing your eye measures directly
-- useful when the story is "how much do these two teams differ," not
just "which bar is longer."
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_team_dumbbell

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)

# %%
fig, ax = plot_team_dumbbell(summary, metric="attempts", title="Attempts by set-piece type")

# %%
fig, ax = plot_team_dumbbell(summary, metric="success_rate", title="Success rate by set-piece type")
