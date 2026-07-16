"""
Corner/free-kick report + radar
==================================

:func:`wa_setpieces.corner_report` (and ``free_kick_report``) merges
attempts, success rate, second-phase rate, retention rate, and -- with a
fitted xT model -- added value and goals into one table per team. Handed
to :func:`~wa_setpieces.viz.plot_set_piece_radar`, it becomes a one-glance
profile comparison, in the same spirit as a scouting radar/pizza chart.
"""

from pathlib import Path

from wa_setpieces import corner_report, free_kick_report, load_events
from wa_setpieces.viz import plot_set_piece_radar
from wa_setpieces.xt import XTModel

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
# The full corner report -- one row per team:
report = corner_report(match.events, model=model)
report

# %%
fig, ax = plot_set_piece_radar(report, title="Corner profile")

# %%
# Same for free kicks:
fk_report = free_kick_report(match.events, model=model)
fig, ax = plot_set_piece_radar(fk_report, title="Free-kick profile")
