"""
Success rate: ring
=====================

The same single-ratio job as
:func:`~wa_setpieces.viz.plots.plot_success_waffle`, in a different
visual metaphor: a circular progress ring instead of a grid of filled
squares -- closer to what a KPI dashboard widget typically looks like.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_success_ring

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)
row = summary[summary["set_piece_type"] == "throw_in"].sort_values("attempts", ascending=False).iloc[0]

# %%
fig, ax = plot_success_ring(
    int(row["successful"]), int(row["attempts"]), label="Throw-in retention",
)
