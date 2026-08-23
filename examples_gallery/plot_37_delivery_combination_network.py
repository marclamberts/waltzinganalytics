"""
Delivery combinations: network
==================================

A node-link graph of who takes deliveries and which teammate usually
wins the first contact, built from
:func:`~wa_setpieces.core.phases.classify_phase`'s own ``first_contact_*``
fields (scoped to contacts the delivering team itself won -- a defender
winning it first isn't a "combination"). Edge width is how often that
pairing happened; node size is how often that player was involved at
all, as either end.

The only chart in this gallery for an open set of players connected by
who-delivers-to-whom, rather than a fixed small set of teams or
categories -- everything else here (radar, parallel coordinates,
dumbbell) compares a handful of known entities, not a graph.
"""

from pathlib import Path

from wa_setpieces import load_matches, set_piece_summary
from wa_setpieces.viz.plots import plot_delivery_combination_network

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
summary = set_piece_summary(events)
team_id = summary["contestantId"].iloc[0]

# %%
fig, ax = plot_delivery_combination_network(events, "free_kick", team_id)
