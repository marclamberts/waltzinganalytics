"""
Light and dark mode
======================

Every plotting function takes ``dark: bool = True`` -- the whole figure
(pitch, chart chrome, team colors) switches between the validated dark and
light palettes in :mod:`wa_setpieces.viz.theme` with that one argument. Both
palettes pass the same colorblind-safety and contrast checks against their
own chart surface (navy for dark, white for light).

The two-team charts (:func:`~wa_setpieces.viz.plot_team_comparison` and
friends) use a fixed orange-then-blue ``team_colors`` convention -- the
first team passed (or the first row in the summary/report, if
``team_order`` isn't given) is always orange, the second always blue,
consistently across a whole report. ``subtitle`` and ``footer`` are
optional: a muted line under the title, and a small credit/source line in
the bottom-right corner of the figure -- never set by default, since a
source credit belongs to whoever is publishing the chart.
"""

from pathlib import Path

from wa_setpieces import delivery_locations, load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_delivery_map, plot_team_comparison

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
corners = delivery_locations(match.events, "corner")
summary = set_piece_summary(match.events)

# %%
# Dark mode (the default):
fig, ax = plot_delivery_map(
    corners, title="Corner deliveries", subtitle="Sample match · Delivery map",
    footer="Data: Opta", dark=True,
)

# %%
# The same figure, light mode:
fig, ax = plot_delivery_map(
    corners, title="Corner deliveries", subtitle="Sample match · Delivery map",
    footer="Data: Opta", dark=False,
)

# %%
# Team comparisons use a fixed orange/blue pairing in both modes:
fig, ax = plot_team_comparison(summary, metric="attempts", title="Attempts by set-piece type", dark=False)
