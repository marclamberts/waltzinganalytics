"""
Second-phase corner sequences
================================

:mod:`wa_setpieces.phases` classifies what happens after a corner is
delivered: was it cleared immediately, did it produce a direct shot, or did
the ball stay alive for a **second-phase shot** (a knockdown, blocked
clearance, or loose ball the attacking team won again before the danger
was cleared).

Note the defending team's events are recorded in *their own* attacking
direction, so we mirror them onto the attacking team's frame with
:func:`wa_setpieces.to_reference_frame` before plotting anything -- see
that function's docstring for how this was verified against the data.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.phases import second_phases
from wa_setpieces.viz import plot_second_phase

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Classify every corner in the match:
corners = second_phases(match.events, "corner")
corners[["delivery_event_id", "cleared_immediately", "second_phase_shot", "phase_events_n"]]

# %%
# Plot the sequence for the first corner that produced a second-phase shot.
# Numbered grey dots are the contested touches after the delivery; the gold
# dot is the shot that eventually resulted.
shot_corners = corners.loc[corners["second_phase_shot"], "delivery_event_id"]
fig, ax = plot_second_phase(match.events, int(shot_corners.iloc[0]))

# %%
# And one that was cleared immediately, for contrast:
cleared = corners.loc[corners["cleared_immediately"], "delivery_event_id"]
if not cleared.empty:
    fig, ax = plot_second_phase(match.events, int(cleared.iloc[0]))
