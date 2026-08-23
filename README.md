# wa-setpieces

> **Work in progress.** This package is under active development, and
> updates will keep coming heavily in the near future. Feedback, bug
> reports, or trouble getting something to work? Reach out at
> marc@waltzinganalytics.com.

Set-piece analytics for football (soccer) matches from **Opta / Stats
Perform**, **StatsBomb**, or **IMPECT** event data — one loading call,
`load_matches(source, provider=...)`, for any of the three, a single
match file or a whole folder (season): penalties, kick-offs, free kicks,
corners, throw-ins and goal kicks.

Given a match file, this package tags every set-piece restart and covers,
end to end: attempt/success counts by team and player, delivery maps,
assist-chain shot/goal linking, second-phase (knockdown/flick-on)
detection, possession retention, pitch zones/thirds/channels, a
grid-based Expected Threat (xT) model, blended added-value scoring,
per-delivery outcome classification (including who wins each aerial
duel), a rule-based *and* a data-driven (k-means) routine taxonomy,
benchmarked 0-100 team/player ratings, defensive conceding profiles
(including an opponent-scouting report), penalty placement, long-throw
specialist detection, season-safe multi-match aggregation with rolling
form, self-contained HTML reports, CSV/Excel export, and pitch plots
built on [mplsoccer](https://mplsoccer.readthedocs.io) — all as tidy
`pandas` DataFrames.

<p align="center">
  <img src="https://raw.githubusercontent.com/marclamberts/waltzinganalytics/main/docs/source/_static/hero_corners.png" alt="Corner delivery map drawn with mplsoccer" width="640">
</p>

**Full documentation, with a runnable plot gallery: https://waltzinganalytics.readthedocs.io**

## By set piece

Pick your set piece, then pick what you want from it. Full breakdown
(including exactly which fields each type returns) is on the
[By set piece](https://waltzinganalytics.readthedocs.io/en/latest/categories.html)
docs page; this table is the fast version.

| Type | Export to CSV/Excel | Metrics to pull | Value model | Visualisation |
| --- | --- | --- | --- | --- |
| **Corner** | [`workflow --type corner --format xlsx`](#command-line) | counts, deliveries, [second phases + retention](#second-phases-xt-zones-retention-added-value-and-outcomes), [routines + clusters](#routines-taxonomy-technique-target-and-clusters) | [xT added value + team/player rating](#ratings) (needs a fitted model) | full [plot set](#plots) + corner sonar + curated [HTML report](#reports-and-exporting) |
| **Free kick** | [`workflow --type free_kick --format xlsx`](#command-line) | same as corner | same as corner (xT added value + rating) | full [plot set](#plots) (no sonar, no curated report) |
| **Throw-in** | [`workflow --type throw_in --format xlsx`](#command-line) | counts, deliveries, retention, [long-throw detection](#long-throws) | not available — rating runs off success/retention rate only | delivery map, zone heatmap, [routine clusters](#plots) |
| **Penalty** | [`workflow --type penalty --format xlsx`](#command-line) | counts, [placement zone + taker conversion](#penalties) | not applicable — rating runs off conversion rate | no dedicated plot yet — read the [placement table](#penalties) |
| **Goal kick** | [`workflow --type goal_kick --format xlsx`](#command-line) | counts, deliveries, retention, routines | not available — rating runs off success/retention rate only | delivery map, zone heatmap, [team comparison](#plots) |
| **Kick off** *(coming soon)* | [`workflow --type kick_off --format xlsx`](#command-line) works today | counts, deliveries, retention, routines — no curated extras yet | not available yet | general plots only — no curated layer yet |

## Install

```bash
pip install wa-setpieces
```

Or install from source:

```bash
git clone https://github.com/marclamberts/waltzinganalytics.git
cd waltzinganalytics
pip install -e .
```

Optional extras, installed as needed throughout this README:
`viz` (plots), `ml` (bundled shot-value models), `convert` (the corners
batch exporter), `xlsx` (Excel export) — e.g. `pip install
"wa-setpieces[viz,ml]"`.

Prefer to run things instead of reading them?
[`examples/full_walkthrough.ipynb`](examples/full_walkthrough.ipynb) is a
single notebook that exercises essentially everything below — loading,
extraction, routines/outcomes/aerial duels, xT and added value, ratings,
defending/opponent scouting, penalties, long throws, season form,
plotting, and CSV/Excel export — against the bundled sample match, with
every cell's real output saved in the notebook.

## Quickstart

```python
from wa_setpieces import load_matches, set_piece_summary

events = load_matches("match.json", provider="opta", type="match")
summary = set_piece_summary(events)
print(summary)
```

```
              contestantId set_piece_type  attempts  successful  success_rate  shots  goals
cxb4hqite921i...      corner         2           1         0.500      0      0
cxb4hqite921i...   free_kick        12           9         0.750      0      0
cxb4hqite921i...   goal_kick         8           5         0.625      0      0
cxb4hqite921i...    kick_off         1           1         1.000      0      0
cxb4hqite921i...    throw_in        20          16         0.800      0      0
...
```

### The whole pipeline in one call

Everything below this section — team/player counts, delivery locations,
second-phase detection, retention, added value, the report, the rating,
defensive conceding profiles, routine clusters, aerial-duel record,
penalty placement, and long-throw analysis — is one function chain most
people want run together. `run_workflow` runs that whole chain for you
and hands back every table at once, instead of wiring a dozen function
calls together yourself:

```python
from wa_setpieces import run_workflow, XTModel

model = XTModel.fit(events)         # optional -- unlocks added value + player rating
result = run_workflow(events, "corner", model=model)

result.summary                    # attempts, success rate, shots, goals
result.deliveries                 # start/end coordinates for a delivery map
result.second_phases              # cleared / first-phase shot / second-phase shot, per corner
result.retention                  # still in possession ~8s later?
result.added_value                # xT added + resulting shot quality + goals, per delivery
result.report                     # all of the above, rolled up per team
result.team_rating                # 0-100 benchmark score per team
result.player_rating              # delivery score / finishing score per player
result.defensive_summary          # attempts/shots/goals conceded, per team
result.defensive_routine_summary  # what a team concedes most, by routine type
result.defensive_zone_summary     # ... by destination zone
result.routine_clusters           # data-driven (k-means) delivery clusters (needs the ml extra)
result.aerial_duel_team_summary   # aerial-duel win rate per team
result.aerial_duel_player_summary # aerial-duel wins per player
```

Fields that don't apply to `set_piece_type` (`deliveries` for a penalty,
`penalty_placement` for a corner, `routine_clusters` without the `ml`
extra installed, ...) are `None` rather than an empty table, so a truthy
check tells you whether that step ran at all. Reach for the individual
functions below directly when you only need one piece, want different
parameters per step, or are combining several matches. `run_workflow`
computes nothing new — it's a convenience wrapper, not a shortcut that
skips anything.

## Second phases, xT, zones, retention, added value and outcomes

```python
from wa_setpieces import (
    second_phases, second_phase_summary,   # corner/free-kick second-phase shots
    retention_detail, retention_rate,      # possession retained N seconds later
    add_thirds, add_channels, add_zone_grid,  # pitch location tagging
    XTModel, set_piece_delivery_xt, set_piece_xt_summary,  # Expected Threat
    set_piece_added_value, set_piece_value_summary,  # xT + shot quality + goals, blended
    corner_report, free_kick_report,       # all of the above, merged into one table per team
    delivery_outcomes, outcome_summary,    # per-delivery outcome, for a shot map
    aerial_duel_summary,                   # who wins each contested header
)

second_phases(events, "corner")           # per-corner: cleared / first-phase shot / second-phase shot
second_phase_summary(events, "free_kick") # per-team roll-up

retention_rate(events, "corner")          # per-team: % of corners where the ball is retained ~8s later

tagged = add_thirds(events)               # defensive_third / middle_third / attacking_third
tagged = add_channels(tagged, n=5)              # wide / half-space / central

model = XTModel.fit(events)               # fit an xT grid (fit on many matches for real use!)
set_piece_xt_summary(events, "corner", model)  # total/average xT added per team

set_piece_added_value(events, "corner", model)  # per-delivery: xT added + resulting shot quality + goal
corner_report(events, model=model)              # attempts, success/retention/second-phase rate, added value -- one table

delivery_outcomes(events, "corner")
# per-delivery `delivery_outcome`: short_corner / direct_shot / second_phase_shot /
# aerial_duel / cleared / first_touch_won / first_touch_lost / no_action, plus
# aerial_winner_contestant_id/_player_id/_player_name when it's an aerial_duel

team_summary, player_summary = aerial_duel_summary(events, "corner")
# team_summary: duels_involved, duels_won, win_rate, per team
# player_summary: duels_won per player who won at least one identified duel
```

An `XTModel` fitted on a season (not one match — see the module docstring
for why) persists whole: every probability grid plus training metadata,
so a fitted model is a portable artifact you train once and reuse:

```python
model.save("league-model.npz")
loaded = XTModel.load("league-model.npz")
loaded.evaluate(held_out_events)  # shot count, goals and Brier score on data it wasn't fit on
```

`wa_setpieces.core.attribution` adds player-level attribution for what
happened right after a delivery, on top of `second_phases`' team-level
view:

```python
from wa_setpieces import first_contact_detail, first_contact_summary

first_contact_detail(events, "corner")
# per-delivery: who touched the ball next (first_contact_player_id/_name,
# _team_id), whether their team won it, and seconds_to_contact --
# explicitly labelled confidence="event_sequence" throughout, since event
# data can prove ordering but not physical contact the way tracking can

first_contact_summary(events, "corner")
# per-player: contacts, contacts_won, win_rate
```

All of the above are **derived heuristics**, not raw Opta fields — see the
[docs](https://waltzinganalytics.readthedocs.io) for the exact assumptions
and tunable thresholds behind each one — in particular
[By phase and outcome](https://waltzinganalytics.readthedocs.io/en/latest/by_phase.html),
which also documents a real bug this uncovered and fixed: the feed's `eventId`
is only unique *within one team's own event stream, per match* — every
delivery/shot lookup in this package is scoped accordingly (including
across matches, where relevant).

## Shot value (experimental)

Five pre-trained gradient-boosted models, bundled with the package, score
every shot in a match:

```bash
pip install -e ".[ml]"   # xgboost + scikit-learn + joblib
```

```python
from wa_setpieces.ml.shot_value import ShotValueModels, shot_value

models = ShotValueModels.load()          # loads once; reuse across matches
shots = shot_value(events, models)
# eventId, playerName, is_goal, set_piece_type, on_target_prob, xgot, psxg,
# situational_prob, outcome_class_0..3, shot_value (blended)
```

**Read `wa_setpieces/ml/shot_value.py`'s module docstring before trusting
this for anything real.** The five models were trained elsewhere against a
feature schema this package has to reconstruct from Opta qualifiers on
each shot event; some inputs (shot geometry, set-piece origin, assist,
left/right foot, goal-mouth placement) are confidently derived from
already-tested logic elsewhere in this package, but several situational
flags (big chance, one-on-one, fast break, scramble, header/volley) have no
reliable qualifier signal in the two real matches this was checked against
and default to `False` rather than a guessed-and-possibly-wrong qualifier
ID — that gap is documented, not hidden, but it does mean predictions are
degraded relative to the models' original training data. The underlying
goal-mouth placement geometry (`wa_setpieces.core.placement.goal_placement`)
is pure qualifier math with no model dependency, and is reused directly by
`core.penalties` for penalty placement (see below) without needing the
`ml` extra.

## Ratings

`wa_setpieces.core.rating` turns a report into a single 0-100 "how good"
score, benchmarked (z-scored) against whoever else is in the table —
**always rate against a full season/competition, not one match**; a
two-row sample just tells you which of those two had the better match, not
how good either team actually is.

```python
from wa_setpieces.core.rating import team_rating, player_rating

team_rating(corner_report(season_events, model=model))
# ... success_rate, avg_added_value, retention_rate, plus a *_score column
# per metric and a composite `rating` (50 = this table's own average)

player_rating(season_events, "corner", model, min_deliveries=5, min_shots=3)
# delivery_score (taker quality) and finishing_score (shooter quality),
# merged -- a pure taker or pure finisher is rated on the component they
# have, not penalized for the one they don't
```

## Routines: taxonomy, technique, target and clusters

`wa_setpieces.core.routines` describes *how* a restart was taken, on top
of what happened afterwards:

```python
from wa_setpieces import restart_routines, routine_summary, all_routine_summaries

restart_routines(events, "corner")
# one row per corner: routine_type, delivery_technique, post_target,
# distance, progression, direction, side, start/end third,
# start/target channel, delivery_outcome, retention, shots, goals

routine_summary(events, "goal_kick")
# usage share and outcome rates for short_build / medium_build / long routines

all_routine_summaries(events)
# one combined tactical inventory covering all six restart types
```

`delivery_technique` (`"inswinger"`/`"outswinger"`, from Opta qualifiers
223/224) and `post_target` (`"near_post"`/`"far_post"`/`"central"`,
relative to which flank the restart was taken from) apply to corners and
free kicks. The type-specific routine families are:

- Corners: short, central six-yard, penalty-area, recycled, deep/edge.
- Free kicks: direct shot, short, box delivery, progressive, recycled, lateral.
- Throw-ins: short, medium, long, with location and progression attached.
- Penalties: scored, saved, post, missed.
- Goal kicks: short build, medium build, long.
- Kick-offs: backward, lateral, short forward, direct long.

For a structured tactical analysis, use one call:

```python
from wa_setpieces import analyze_routines

analysis = analyze_routines(events, "corner", min_taker_attempts=3)
analysis.detail          # every routine and its geometry/outcome
analysis.summary         # routine-family usage and efficiency
analysis.team_profiles   # diversity, predictability and preferred patterns
analysis.taker_profiles  # taker preferences and creation results
analysis.target_matrix   # routine family -> destination zone -> outcomes
```

`detail` also includes approximate distance in metres, delivery angle,
verticality, a tactical destination zone, and a stable `routine_key`
combining family, side and destination. Multi-match frames with
`matchId` are automatically separated before temporal analysis.

As an alternative to that fixed, hand-picked taxonomy, `cluster_routines`
groups deliveries by geometric similarity (k-means) instead — surfacing
whatever patterns a team actually repeats:

```bash
pip install -e ".[ml]"   # scikit-learn
```

```python
from wa_setpieces import cluster_routines, cluster_summary

clustered = cluster_routines(events, "corner", n_clusters=5)
# restart_routines' detail plus `cluster` (int) and an auto-generated
# `cluster_label` (e.g. "short, forward, central")
cluster_summary(clustered)  # per-cluster usage/outcome roll-up
```

### Long throws

The one throw-in pattern that plays like a corner:

```python
from wa_setpieces import long_throw_taker_summary, long_throw_second_phases

long_throw_taker_summary(events, min_distance=25.0)
# per-player usage share and threat created (shots/goals via the
# assist-chain link) among throw-ins that travel far enough to threaten

long_throw_second_phases(events, min_distance=25.0)
# event-sequence-based flick-on/knockdown detection, restricted to the
# same long throws -- the throw-in equivalent of second_phases()
```

### Penalties

```python
from wa_setpieces import penalty_placement_detail, penalty_taker_summary

penalty_placement_detail(events)
# per-penalty result (scored/saved/post/missed) and placement zone in
# the goal frame (goal_y_norm, goal_h_norm, corner_zone 0-8, placement_score)

penalty_taker_summary(events)
# per-taker attempts, result breakdown, conversion rate, avg placement score
```

## Defending, opponent scouting and season form

```python
from wa_setpieces import (
    defensive_set_piece_summary, defensive_rating,
    defensive_routine_summary, defensive_zone_summary,
)

defensive_set_piece_summary(events)     # attempts/shots/goals conceded, per team
defensive_routine_summary(events, "corner")  # ... broken down by routine type conceded
defensive_zone_summary(events, "corner")     # ... broken down by destination zone conceded
defensive_rating(defensive_set_piece_summary(events))  # 0-100, lower concessions score better
```

Pre-match scouting on how an opponent *defends* a set-piece type, as a
ready-to-view HTML report:

```python
from pathlib import Path
from wa_setpieces import opponent_scouting_report_html

html = opponent_scouting_report_html(events, opponent_id="...", set_piece_type="corner")
Path("scouting.html").write_text(html, encoding="utf-8")
```

`SeasonDataset` makes multi-match aggregation safe by requiring a
`matchId` boundary (`validate_events(..., require_match_id=True)` on
construction) and running every temporal heuristic within each match
rather than across the combined frame:

```python
from wa_setpieces import SeasonDataset

season = SeasonDataset.from_sources(paths)  # matchId defaults to each file's stem
season.summary()                       # competition totals and per-match rates
season.report("corner", model)         # match-level report rows -- one per (team, match)
season.season_report("corner", model)  # the same fields, rolled up into one row per team
season.rolling_summary(window=5)            # rolling attacking form
season.rolling_defensive_summary(window=5)  # rolling defensive form (conceding side)
```

`rolling_summary`/`rolling_defensive_summary` are only meaningful if
`paths`/`match_ids` were supplied to `from_sources` already in
chronological order — there's no date field in the loaded event schema
to derive true match order from otherwise. `from_sources` refuses two
sources that resolve to the same `matchId` (e.g. two different
directories both containing a same-named file) rather than silently
merging them into one match.

`validate_events` documents and checks the provider-neutral event contract
every module in this package assumes; `event_capabilities` reports which
optional information a given adapter (Opta vs StatsBomb) actually supplies.

## Command line

```bash
wa-setpieces match.json
wa-setpieces match.json --csv summary.csv
wa-setpieces match.json --xt   # also fit + print xT for this match (illustrative on one match)
```

The command-line interface also exposes the complete workflow:

```bash
wa-setpieces summary match.json --output summary.json --format json
wa-setpieces train-xt season/*.json --output league-model.npz
wa-setpieces workflow match.json --type corner --model league-model.npz --output tables/ --format xlsx
wa-setpieces report match.json --type corner --model league-model.npz --output report.html
wa-setpieces scout match.json --opponent <contestantId> --type corner --output scouting.html
wa-setpieces season match_1.json match_2.json ... --action season-report --type corner --output season.csv
```

`workflow` exports every table `run_workflow` produces — including the
defensive, routine-cluster, aerial-duel, penalty and long-throw tables
above — as one CSV (default) or Excel (`--format xlsx`) file per table,
with no extra flags needed. `report --type corner` writes the curated
report above (rating, outcome/routine breakdowns, delivery/outcome maps
if `viz` is installed); other `--type`s fall back to a generic dump of
every workflow table since there's no equivalent curated report for them
yet. `scout` writes an [opponent scouting report](#defending-opponent-scouting-and-season-form)
for one team. `season` runs [`SeasonDataset`](#defending-opponent-scouting-and-season-form)
over every file given (each tagged with its own filename as `matchId` —
distinct filenames required, or it refuses rather than silently merging
two matches into one) — `--action` is one of `summary`, `report`
(match-level rows), `season-report` (whole-season roll-up), `rolling` or
`rolling-defense` (`--window` trailing matches). Use `--provider
statsbomb` with any command for a StatsBomb events export. Outputs
support CSV, JSON and Parquet where applicable; for CSV or Excel from
Python directly, see `save_table`/`save_tables` below.

## Reports and exporting

Self-contained, portable HTML reports for corners (`corner_report_html`)
and opponent scouting (`opponent_scouting_report_html`, see above) —
tables plus delivery maps/shot maps when the `viz` extra is installed,
degrading gracefully to tables-only otherwise:

```python
from pathlib import Path
from wa_setpieces import corner_report_html

html = corner_report_html(events, model=model)  # a ready-to-write HTML string
Path("corner_report.html").write_text(html, encoding="utf-8")
```

Any table this package produces can be saved to CSV or Excel, chosen by
file extension:

```bash
pip install -e ".[xlsx]"   # openpyxl, for .xlsx/.xls output
```

```python
import pandas as pd
from wa_setpieces import save_table, save_tables

save_table(corner_report(events, model=model), "corner_report.xlsx")

# One file per SetPieceWorkflow table (skip the non-table fields, e.g. set_piece_type):
tables = {name: value for name, value in vars(result).items() if isinstance(value, pd.DataFrame)}
save_tables(tables, "workflow_tables/", fmt="csv")
```

## Other data providers

`load_matches(source, provider="opta", type="match")` is the one loading
entry point for every provider — Opta (native, no conversion needed),
StatsBomb, or IMPECT — and either scope, one match file or a whole folder
(a season). Every call takes the same two keywords, `provider` and
`type`, so nothing else about the call changes shape between them.
`wa_setpieces.providers` does the actual per-provider conversion into the
same internal frame Opta produces, so every other module — filters,
metrics, chains, phases, retention, xT, value, rating, routines,
defending, viz — works unchanged regardless of source:

```python
from wa_setpieces import load_matches, set_piece_summary

load_matches("match.json", provider="opta", type="match")
load_matches("statsbomb_events_export.json", provider="statsbomb", type="match")
load_matches("impect_export.csv", provider="impect", type="match")   # often many matches in one export already
load_matches("season/", provider="statsbomb", type="season")         # a whole folder, combined

events = load_matches("statsbomb_events_export.json", provider="statsbomb", type="match")
set_piece_summary(events)  # same functions, same DataFrame shape, regardless of provider
```

Read `wa_setpieces/providers/statsbomb.py`'s and
`wa_setpieces/providers/impect.py`'s module docstrings for exactly what
is (and isn't) faithfully mapped for each — set-piece detection, the
assist-chain shot link, retention, xT and rating are all faithful for
both; each has its own narrow, documented edge cases (StatsBomb: one
second-phase-timing approximation; IMPECT: no player-name field, no
delivery-technique field). The IMPECT converter was built and verified
against a real 20-match export, not a schema guess.

## Plots

```bash
pip install -e ".[viz]"   # matplotlib + mplsoccer
```

```python
from wa_setpieces.viz.plots import (
    plot_delivery_map,      # arrow map of deliveries, colored by outcome
    plot_zone_heatmap,      # where events happen, gridded onto the pitch
    plot_xt_grid,           # a fitted XTModel's grid, as a heatmap
    plot_second_phase,      # one corner/free-kick's phase sequence, numbered
    plot_team_comparison,   # grouped bars: both teams, every set-piece type
    plot_xt_added_bars,     # diverging bar chart of xT added per delivery
    plot_corner_sonar,      # polar plot of delivery angle + distance
    plot_match_timeline,    # every set piece on one shared match-minute axis
    plot_dashboard,         # one-figure report card combining several of the above
    plot_set_piece_radar,   # two-team radar over a corner_report/free_kick_report
    plot_set_piece_outcomes,  # shot map: every delivery, colored by outcome
    plot_rating_benchmark,   # team/player rating vs. the sample-average baseline
    plot_routine_clusters,   # delivery map colored by cluster_routines' clusters
    plot_defensive_routine_bars,  # what a team concedes most, by routine or zone
    plot_aerial_duel_win_rate,    # per-team aerial-duel win rate
)

plot_delivery_map(
    delivery_locations(events, "corner"), title="Corner deliveries",
    subtitle="20 June 2026 · Delivery map", footer="Data: Opta", dark=False,  # or dark=True (default)
)
plot_dashboard(events, team_id, set_piece_type="corner")  # the "hero" figure
plot_set_piece_radar(corner_report(events, model=model))  # team A vs. team B, one glance
plot_rating_benchmark(team_rating(corner_report(season_events, model=model)))
```

Every plotting function returns `(fig, ax)` (`plot_dashboard` returns just
`fig`, being multi-panel) for further customization, and takes `dark: bool
= True` -- the whole figure switches between the Waltzing Analytics dark
(navy/coral) and light (paper/amber) house-style palette with that one
argument, see `wa_setpieces.viz.theme.get_palette`. Colors are assigned by
the job they do — a categorical palette for team identity (team-vs-team
charts use a fixed teal-then-blue pairing in both modes), a status pair
for success/fail, gold for goals, single-hue sequential ramps for
magnitude, and a diverging pair for signed quantities like xT added — not
picked for looks; see `wa_setpieces/viz/theme.py`.

Every plot also carries the WA card anatomy: an optional `eyebrow`
(a small category label above the title, e.g. `"Corner"`), a serif
`title`, a muted `subtitle` line beneath it, the "WA · WALTZING ANALYTICS"
brand lockup top-right (on by default -- this package's own brand mark,
not the caller's), and a footer with an optional `footer` source/credit
line bottom-left. Pass `author="Your Name"` to add a byline under the
lockup and a "Your Name | Created on DD-MM-YYYY" stamp to the footer --
there's no default author, so a chart from this package always carries
the WA mark but never a name that isn't yours. See the
[gallery](https://waltzinganalytics.readthedocs.io/en/latest/gallery/index.html)
for these in action, in both modes, with full source code.

## Video clips

Clip in/out timestamp windows (match-clock seconds) for every delivery of
any set-piece type, for handing off to a video-clipping tool:

```python
from wa_setpieces.core.clips import delivery_clip_windows

delivery_clip_windows(events, "corner", pre_seconds=5, post_seconds=15)
# eventId, contestantId, playerId, playerName, periodId, timeMin, timeSec,
# event_seconds, clip_start_seconds, clip_end_seconds
```

## What counts as a set piece

| Type        | Detected on                              | Opta qualifierId |
|-------------|---------------------------------------------|-------------------|
| Penalty     | shot event (miss/post/saved/goal)          | 9                 |
| Kick-off    | pass event                                 | 279               |
| Free kick   | pass event (corners excluded)              | 5                 |
| Corner      | pass event                                 | 6                 |
| Throw-in    | pass event                                 | 107                |
| Goal kick   | pass event                                 | 124               |

These qualifier IDs are the standard Opta/Stats Perform vocabulary and
were cross-checked against a real match export (see `tests/data/sample_match.json`
and `tests/test_filters.py`): tagged events line up with their expected pitch
location (corner arc, touchline, centre spot, six-yard line).

## Package layout

- `wa_setpieces.core.loader` — parse Opta JSON into a tidy `pandas.DataFrame`; `load_matches` is the one entry point for any provider, a single file or a whole season folder; `load_events_multi` stacks several already-known Opta sources.
- `wa_setpieces.core.constants` — Opta typeId / qualifierId reference.
- `wa_setpieces.core.schema` — `validate_events`/`event_capabilities`: the provider-neutral event contract every module assumes.
- `wa_setpieces.core.filters` — extract/tag each set-piece type.
- `wa_setpieces.core.metrics` — team/player counts, success rates, delivery locations.
- `wa_setpieces.core.chains` — link set pieces to the shots/goals they produced.
- `wa_setpieces.core.zones` — pitch thirds, channels and a configurable zone grid.
- `wa_setpieces.core.phases` — second-phase detection for corners/free kicks.
- `wa_setpieces.core.retention` — possession retention after any restart.
- `wa_setpieces.core.xt` — grid-based Expected Threat (xT), fit from data.
- `wa_setpieces.core.value` — set-piece added value: delivery xT + resulting shot quality + goals, blended.
- `wa_setpieces.core.outcomes` — per-delivery `delivery_outcome` classification (short corner, direct/second-phase shot, aerial duel, cleared, first/lost touch) for a shot-map scatter, plus `aerial_duel_summary` for who wins the 50/50s.
- `wa_setpieces.core.placement` — shared goal-mouth shot placement geometry (used by `ml.shot_value` and `core.penalties`); pure qualifier math, no model dependency.
- `wa_setpieces.core.penalties` — `penalty_placement_detail`/`penalty_taker_summary`: penalty result and placement zone.
- `wa_setpieces.core.routines` — `restart_routines`'s rule-based taxonomy (including `delivery_technique`/`post_target` for corners/free kicks), `cluster_routines`/`cluster_summary` for a data-driven (k-means) alternative (optional `ml` extra), and `long_throw_taker_summary`/`long_throw_second_phases` for long-throw specialists.
- `wa_setpieces.core.attribution` — `first_contact_detail`/`first_contact_summary`: event-sequence-based player attribution after a delivery.
- `wa_setpieces.ml.shot_value` — five bundled pre-trained models (on-target probability, xGOT, post-shot xG, situational quality, outcome class) for a richer per-shot value score (optional `ml` extra; **experimental**, read the module docstring).
- `wa_setpieces.core.report` — `corner_report`/`free_kick_report`: everything above, merged into one table per team.
- `wa_setpieces.core.rating` — benchmarked 0-100 team/player "how good" scores from a report (see Ratings above).
- `wa_setpieces.core.defending` — `defensive_set_piece_summary`/`defensive_rating`, plus `defensive_routine_summary`/`defensive_zone_summary` for what a team concedes by routine type or destination zone.
- `wa_setpieces.core.season` — `SeasonDataset`: match-safe multi-match aggregation, rolling attacking/defensive form.
- `wa_setpieces.core.workflow` — `run_workflow`: the whole pipeline above, one function call (see "The whole pipeline in one call").
- `wa_setpieces.core.clips` — `delivery_clip_windows`: clip in/out timestamps per delivery, for video-clipping tools.
- `wa_setpieces.reporting` — `corner_report_html`/`opponent_scouting_report_html`/`render_html_report`/`write_html_report`: portable self-contained HTML reports; `save_table`/`save_tables`: CSV/Excel export for any table.
- `wa_setpieces.providers.statsbomb` — convert a StatsBomb open-data export into the same internal frame Opta produces.
- `wa_setpieces.viz.plots` — mplsoccer/matplotlib plots: delivery maps, heatmaps, sonar, timeline, dashboard, radar, rating benchmark, routine clusters, defensive conceding bars, aerial-duel win rate (optional `viz` extra).
- `wa_setpieces.viz.theme` — the validated dark/light color palettes every plot draws from.
- `wa_setpieces.convert.corners` — batch-convert a directory of Opta exports plus a match-list CSV into a flat corners table for tools that expect that schema (optional `convert` extra).
- `wa_setpieces.cli` — `wa-setpieces` command-line tool.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Releasing

Publishing to PyPI is automated via GitHub Actions trusted publishing
(`.github/workflows/publish.yml`) — no API token stored anywhere. **One-time
setup** (only a PyPI project owner can do this, since it requires logging
into PyPI):

1. On PyPI: <https://pypi.org/manage/account/publishing/> → add a pending
   trusted publisher with project name `wa-setpieces`, owner
   `marclamberts`, repository `waltzinganalytics`, workflow `publish.yml`,
   environment `pypi`.
2. From then on, publishing a GitHub Release (or pushing a `v*` tag) builds
   the sdist/wheel and uploads them automatically.

## Docs

Docs are built with Sphinx (`sphinx-rtd-theme` + `sphinx-gallery`, the
same stack mplsoccer's docs use) and hosted on Read the Docs
(`.readthedocs.yaml` at the repo root). The gallery under `examples_gallery/`
is executed at build time, so its plots and DataFrame outputs are always
current. To build locally:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/_build/html
```

## License

MIT
