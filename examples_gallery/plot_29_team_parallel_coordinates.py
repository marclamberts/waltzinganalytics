"""
Team profile: parallel coordinates
======================================

The same two-team profile comparison as
:func:`~wa_setpieces.viz.plots.plot_set_piece_radar`, on straight
parallel axes instead of a circle. A radar's polar layout visually
exaggerates whichever metric lands on the outer ring and compresses
whichever lands near the center, purely from axis placement -- parallel
axes give every metric equal visual weight, and turn "who leads on
what" into reading where the two lines cross, rather than comparing two
overlapping polygon shapes.
"""

from pathlib import Path

from wa_setpieces import corner_report, load_matches
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_team_parallel_coordinates

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
model = XTModel.fit(events, x_bins=8, y_bins=6)
report = corner_report(events, model=model)

# %%
fig, ax = plot_team_parallel_coordinates(report, title="Corner profile comparison")
