"""
KPI scorecard: bullet charts
================================

A compact bullet/KPI chart for a single ratio against qualitative
poor/fair/good bands and an optional target -- built for a dashboard
strip where several of these stack into a scorecard, unlike
:func:`~wa_setpieces.viz.plots.plot_success_waffle`'s big single-ratio
treatment for the same kind of number.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_kpi_bullet

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)
row = summary[summary["set_piece_type"] == "free_kick"].sort_values("attempts", ascending=False).iloc[0]

# %%
fig, ax = plot_kpi_bullet(
    float(row["success_rate"]), target=0.6, label="Free-kick success rate",
)

# %%
# A benchmark a team is *missing*, not clearing, reads just as clearly --
# the tick still marks the same target, the bar just falls short of it:
row2 = summary[summary["set_piece_type"] == "corner"].sort_values("attempts", ascending=False).iloc[0]
fig, ax = plot_kpi_bullet(
    float(row2["success_rate"]), target=0.5, label="Corner success rate",
)
