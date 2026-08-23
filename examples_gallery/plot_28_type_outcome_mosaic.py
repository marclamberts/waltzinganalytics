"""
Type and outcome: mosaic
============================

A Marimekko-style mosaic: set-piece type along the x-axis with each
segment's *width* proportional to how often a team used it, and within
each segment a stacked block whose *height* splits successful from
unsuccessful. Volume and quality in one chart -- a type that's both a
wide slab (a lot of attempts) and mostly red (low success) is the one
worth fixing first, and it's the single most visually obvious thing
here.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_type_outcome_mosaic

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)
team_id = summary["contestantId"].iloc[0]

# %%
fig, ax = plot_type_outcome_mosaic(summary, team_id=team_id, title="Set pieces by type and outcome")
