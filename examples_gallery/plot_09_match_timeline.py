"""
Match timeline
================

Every set piece in the match, laid out on one shared timeline -- one row
per restart type, one dot per delivery, positioned by match minute. Good
for spotting patterns like a team leaning on throw-ins early or corners
piling up late.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.viz import plot_match_timeline

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
fig, ax = plot_match_timeline(match.events)
