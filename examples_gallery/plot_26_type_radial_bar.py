"""
Restart profile: radial bars
================================

Attempts by set-piece type as a wind-rose bar chart -- one bar per type,
arranged clockwise from the top instead of stacked along a shared axis.
Every type gets equal visual weight regardless of label length or value,
and the whole thing reads as a *shape*, a team's restart profile, rather
than a ranked list.

Compare against :func:`~wa_setpieces.viz.plots.plot_team_comparison`'s
horizontal bars for the same underlying numbers -- same data, a
different read.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_type_radial_bar

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)
team_id = summary["contestantId"].iloc[0]

# %%
fig, ax = plot_type_radial_bar(summary, team_id=team_id, metric="attempts", title="Restart profile")
