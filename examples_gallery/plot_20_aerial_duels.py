"""
Aerial duel win rate at corners
===================================

Every ``aerial_duel`` category delivery in ``delivery_outcomes`` now
identifies who actually won the header, from the raw Opta Aerial event's
own outcome flag. ``aerial_duel_summary`` rolls that up into a per-team win
rate and a per-player win count.
"""

from pathlib import Path

from wa_setpieces import load_matches
from wa_setpieces.core.outcomes import aerial_duel_summary
from wa_setpieces.viz.plots import plot_aerial_duel_win_rate

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)

# %%
team_summary, player_summary = aerial_duel_summary(events, "corner")
team_summary

# %%
player_summary

# %%
fig, ax = plot_aerial_duel_win_rate(team_summary)
