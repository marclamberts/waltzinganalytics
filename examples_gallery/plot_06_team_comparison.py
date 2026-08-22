"""
Team comparison: bars and a volume-vs-quality quadrant
==========================================================

Two non-pitch views. First, attempts and success rate for both teams,
across every set-piece type, side by side -- colors follow the fixed
categorical order (team A always the first slot, team B the second)
rather than being picked per chart, so the same team reads as the same
color everywhere.

Second, a question bars can't answer directly: does a team's *volume* of
a given set-piece type actually buy *quality* -- or is the type they do
most also the one that works least. One point per set-piece type, split
into quadrants by the median.
"""

from pathlib import Path

from wa_setpieces import load_events, set_piece_summary
from wa_setpieces.viz.plots import plot_team_comparison, plot_volume_quality_scatter

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)
summary = set_piece_summary(match.events)

# %%
fig, ax = plot_team_comparison(summary, metric="attempts", title="Attempts by set-piece type")

# %%
fig, ax = plot_team_comparison(
    summary, metric="success_rate", title="Success rate by set-piece type"
)

# %%
# One team's own set-piece types, plotted as volume (attempts) against
# quality (success rate) -- bottom-left is the type this team takes often
# *and* converts poorly, the clearest "fix this" signal a bar chart alone
# doesn't surface:
team_id = summary["contestantId"].iloc[0]
team_summary = summary[summary["contestantId"] == team_id]
fig, ax = plot_volume_quality_scatter(
    team_summary, title="Volume vs quality by set-piece type", subtitle=f"Team {team_id[:8]}…",
)
