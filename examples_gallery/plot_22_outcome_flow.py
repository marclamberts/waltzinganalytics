"""
Outcome flow
==============

A Sankey-style view of every delivery: from the restart, through its
:func:`~wa_setpieces.core.outcomes.delivery_outcomes` category, down to
whether it ended in a goal. Every other chart in this gallery ranks,
compares, or maps a set of numbers -- this one shows a *funnel*: how much
of the traffic at the left edge actually survives to a goal at the
right edge.

Ribbon width is proportional to delivery count at every stage, so a
category that rarely converts (most of them) reads as a wide band
flowing straight into "No goal," while anything that does convert shows
up as a visible diagonal sliver breaking off toward "Goal."
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.outcomes import delivery_outcomes
from wa_setpieces.viz.plots import plot_outcome_flow

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Corners in this sample match: no goal came from any of them, so every
# band flows straight through to "No goal" with no diagonal split -- a
# real (if unglamorous) finding a bar chart of counts wouldn't make as
# immediately obvious.
corner_outcomes = delivery_outcomes(match.events, "corner")
fig, ax = plot_outcome_flow(corner_outcomes, title="Corner outcome flow")

# %%
# Free kicks, the same way:
fk_outcomes = delivery_outcomes(match.events, "free_kick")
fig, ax = plot_outcome_flow(fk_outcomes, title="Free-kick outcome flow")
