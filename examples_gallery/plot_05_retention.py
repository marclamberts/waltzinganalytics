"""
Possession retention after a restart
=======================================

:mod:`wa_setpieces.retention` asks a broader question than the raw pass
``outcome`` flag: did the team that took the set piece still have the ball
~8 seconds later, regardless of whether the very first pass found a
teammate. Not every plot needs a pitch underneath it -- a simple bar chart
reads better for a team-by-team comparison.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from wa_setpieces import load_events
from wa_setpieces.retention import retention_rate

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
rates = retention_rate(match.events, "throw_in")
rates

# %%
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(
    [c[:8] + "…" for c in rates["contestantId"]],
    rates["retention_rate"],
    color=["#4c9a5b", "#2e7d9e"],
)
ax.set_ylim(0, 1)
ax.set_ylabel("Throw-in retention rate")
ax.set_title("Possession retained ~8s after a throw-in")
fig.tight_layout()
