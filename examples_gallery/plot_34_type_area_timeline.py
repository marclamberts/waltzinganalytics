"""
Set-piece volume: stacked area
==================================

A stacked area chart of set-piece attempts over match time, binned into
15-minute windows, one band per type -- a *volume* read of the match:
which restart types made up the bulk of the traffic in each phase of
the game, and whether that mix shifted. Different from
:func:`~wa_setpieces.viz.plots.plot_match_timeline`'s individual dots
(unaggregated) and :func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow`'s
cumulative line (one signed value, not a volume breakdown by type).
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.viz.plots import plot_type_area_timeline

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
fig, ax = plot_type_area_timeline(match.events, title="Set-piece volume through the match")
