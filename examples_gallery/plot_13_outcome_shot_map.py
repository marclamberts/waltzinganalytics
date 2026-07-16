"""
Outcome shot map
==================

A colored-scatter "shot map" for set pieces: every corner/free-kick
delivery, plotted where the outcome happened and colored by what that
outcome was -- short corner, direct shot, second-phase shot, aerial duel
("50/50"), cleared, or which team won the first touch. Goals get a ring
around the marker.

:mod:`wa_setpieces.outcomes` builds this on top of
:mod:`wa_setpieces.phases`, adding short-corner detection (a short pass
along the byline rather than a cross -- inferred from delivery distance,
since a corner starts right at the corner arc already) and aerial-duel
detection (``typeId`` 44, a contested header -- football's "50/50").
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.outcomes import delivery_outcomes, outcome_summary
from wa_setpieces.viz import plot_set_piece_outcomes

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Every corner, classified:
corner_outcomes = delivery_outcomes(match.events, "corner")
corner_outcomes

# %%
fig, ax = plot_set_piece_outcomes(corner_outcomes, title="Corner outcomes")

# %%
# Free kicks spread across the whole pitch, not just the box -- they're
# taken from wherever the foul was:
fk_outcomes = delivery_outcomes(match.events, "free_kick")
fig, ax = plot_set_piece_outcomes(fk_outcomes, title="Free-kick outcomes")

# %%
# Rolled up per team:
outcome_summary(match.events, "corner")
