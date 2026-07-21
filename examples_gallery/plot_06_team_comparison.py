"""
Team comparison bars
=======================

A non-pitch view: attempts and success rate for both teams, across every
set-piece type, side by side. Colors follow the fixed categorical order
(team A always the first slot, team B the second) rather than being picked
per chart, so the same team reads as the same color everywhere.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_team_comparison

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)

# %%
fig, ax = plot_team_comparison(summary, metric="attempts", title="Attempts by set-piece type")

# %%
fig, ax = plot_team_comparison(
    summary, metric="success_rate", title="Success rate by set-piece type"
)
