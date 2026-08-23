"""
First half vs second half: slope chart
==========================================

Each set-piece type's value in the first half versus the second, as a
two-point connected line -- a genuinely different temporal comparison
than :func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow`'s
continuous cumulative curve. Collapsing the match down to exactly two
snapshots makes each type's *direction of change* the thing the eye
reads directly from the line's slope: green for more of it after the
break, red for less, gray for no change at all (not colored green, even
though the line is flat -- "unchanged" isn't "improved").
"""

from pathlib import Path

from wa_setpieces import load_matches, set_piece_summary
from wa_setpieces.viz.plots import plot_half_comparison_slope

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
summary = set_piece_summary(events)
team_id = summary["contestantId"].iloc[0]

# %%
fig, ax = plot_half_comparison_slope(events, team_id=team_id)
