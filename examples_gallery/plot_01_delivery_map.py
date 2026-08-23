"""
Delivery map
==============

The starting point for almost any set-piece question: every delivery, drawn
as an arrow from the restart to where it ended up, colored by whether it
found a teammate. The headline stat strip (on by default) states the
takeaway before you've even read the pitch -- how many, and what share
worked.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_matches
from wa_setpieces.viz.plots import plot_delivery_map

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)
corners = delivery_locations(events, "corner")

# %%
fig, ax = plot_delivery_map(corners, title="Corner deliveries")

# %%
# ``density=True`` shades a kernel-density estimate of where deliveries
# land underneath the arrows -- meaningful once there's a season's worth
# of deliveries behind it, not a single match's handful (see the function
# docstring for why it defaults off):
fig, ax = plot_delivery_map(corners, title="Corner deliveries", subtitle="With density", density=True)

# %%
# The same function works on any pass-based set piece -- free kicks:
free_kicks = delivery_locations(events, "free_kick")
fig, ax = plot_delivery_map(free_kicks, title="Free-kick deliveries")
