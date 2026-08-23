"""
Success rate: waffle
=======================

A single headline ratio -- throw-in retention rate for one team -- as a
filled-square icon array instead of a bare percentage. "27 out of 30
squares filled" carries more visual weight than "90%" does buried in a
stat strip, which is the point: reach for this when one ratio *is* the
finding you want the reader to sit with.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_success_waffle

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)
row = summary[summary["set_piece_type"] == "throw_in"].sort_values("attempts", ascending=False).iloc[0]

# %%
fig, ax = plot_success_waffle(
    int(row["successful"]), int(row["attempts"]), title="Throw-in retention rate",
)
