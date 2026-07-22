"""
Team and player set-piece ratings
====================================

:mod:`wa_setpieces.core.rating` turns a set-piece report into a single
0-100 "how good" score: each metric (success rate, added value, retention)
is z-scored against the sample it's given -- 50 is that sample's own
average, not a universal benchmark, so always rate against a full
season/competition, not one match (see the module docstring).

Player ratings split into a delivery score (taker quality) and a
finishing score (shooter quality), since a player can be good at one and
never do the other.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.core.rating import player_rating, team_rating
from wa_setpieces.core.report import corner_report
from wa_setpieces.core.xt import XTModel
from wa_setpieces.viz.plots import plot_rating_benchmark

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
model = XTModel.fit(match.events, x_bins=8, y_bins=6)

# %%
# Team rating -- benchmarked against the (two) teams in this sample match;
# a real report is only meaningful over a full season:
report = corner_report(match.events, model=model)
team_rated = team_rating(report)
team_rated[["contestantId", "success_rate", "avg_added_value", "rating"]]

# %%
# As a benchmark chart:
fig, ax = plot_rating_benchmark(team_rated, title="Corner rating — by team")

# %%
# Player rating -- delivery score and finishing score, merged:
player_rated = player_rating(match.events, "corner", model, min_deliveries=1, min_shots=1)
player_rated[["playerName", "delivery_score", "finishing_score", "rating"]]

# %%
fig, ax = plot_rating_benchmark(
    player_rated, label_col="playerName", title="Corner rating — by player"
)
