"""
The whole pipeline in one call
==================================

Extraction, team/player counts, second-phase detection, retention, added
value, the report, and the rating are normally five-plus function calls
chained together. :func:`wa_setpieces.run_workflow` runs that whole chain
for one set-piece type and hands back every table at once -- this example
runs it, then plots straight off the result.
"""

from pathlib import Path

from wa_setpieces import load_events, run_workflow
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_dashboard, plot_rating_benchmark

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
# One call gets everything -- summary through rating:
result = run_workflow(match.events, "corner", model=model, min_deliveries=1, min_shots=1)
result.report

# %%
# Straight into a plot, no intermediate wiring:
team_id = result.report["contestantId"].iloc[0]
fig = plot_dashboard(match.events, team_id, set_piece_type="corner")

# %%
fig, ax = plot_rating_benchmark(result.team_rating, title="Corner rating — by team")
