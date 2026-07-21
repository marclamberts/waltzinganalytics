# wa-setpieces

Set-piece metrics for football (soccer) matches from **Opta / Stats Perform F24**
event-feed JSON exports: penalties, kick-offs, free kicks, corners,
throw-ins and goal kicks.

Given a raw F24 match file, this package tags every set-piece restart,
aggregates attempts/success rates by team and player, tracks pass end
locations for delivery maps, and links each set piece to the shot or goal
it produced (via Opta's assist-chain qualifier). It also covers, for
corners and free kicks specifically: second-phase detection, Expected
Threat (xT), pitch zones/thirds/channels, and possession retention —
with pitch plots built on [mplsoccer](https://mplsoccer.readthedocs.io).

<p align="center">
  <img src="https://raw.githubusercontent.com/marclamberts/waltzinganalytics/main/docs/source/_static/hero_corners.png" alt="Corner delivery map drawn with mplsoccer" width="640">
</p>

**Full documentation, with a runnable plot gallery: https://waltzinganalytics.readthedocs.io**

## Install

```bash
pip install wa-setpieces
```

Not yet published to PyPI? Install from source instead:

```bash
git clone https://github.com/marclamberts/waltzinganalytics.git
cd waltzinganalytics
pip install -e .
```

## Quickstart

```python
from wa_setpieces import load_events, set_piece_summary

match = load_events("match.json")
summary = set_piece_summary(match.events)
print(summary)
```

```
              contestantId set_piece_type  attempts  successful  success_rate  shots  goals
cxb4hqite921i...      corner         2           1         0.500      1      0
cxb4hqite921i...   free_kick        12           9         0.750      0      0
cxb4hqite921i...   goal_kick         8           5         0.625      0      0
cxb4hqite921i...    kick_off         1           1         1.000      0      0
cxb4hqite921i...    throw_in        20          16         0.800      1      0
...
```

## Second phases, xT, zones, retention, added value and outcomes

```python
from wa_setpieces import (
    second_phases, second_phase_summary,   # corner/free-kick second-phase shots
    retention_detail, retention_rate,      # possession retained N seconds later
    add_thirds, add_channels, add_zone_grid,  # pitch location tagging
    XTModel, set_piece_delivery_xt, set_piece_xt_summary,  # Expected Threat
    set_piece_added_value, set_piece_value_summary,  # xT + shot quality + goals, blended
    corner_report, free_kick_report,       # all of the above, merged into one table per team
    delivery_outcomes, outcome_summary,    # per-delivery outcome category, for a shot map
)

second_phases(match.events, "corner")           # per-corner: cleared / first-phase shot / second-phase shot
second_phase_summary(match.events, "free_kick") # per-team roll-up

retention_rate(match.events, "corner")          # per-team: % of corners where the ball is retained ~8s later

tagged = add_thirds(match.events)               # defensive_third / middle_third / attacking_third
tagged = add_channels(tagged, n=5)              # wide / half-space / central

model = XTModel.fit(match.events)               # fit an xT grid (fit on many matches for real use!)
set_piece_xt_summary(match.events, "corner", model)  # total/average xT added per team

set_piece_added_value(match.events, "corner", model)  # per-delivery: xT added + resulting shot quality + goal
corner_report(match.events, model=model)              # attempts, success/retention/second-phase rate, added value -- one table

delivery_outcomes(match.events, "corner")  # per-delivery: short_corner / direct_shot / second_phase_shot /
                                            # aerial_duel (50/50) / cleared / first_touch_won / first_touch_lost
```

All of the above are **derived heuristics**, not raw Opta fields — see
`docs/source/advanced.rst` (or the hosted docs) for the exact assumptions
and tunable thresholds behind each one. That page also documents a real bug
this uncovered and fixed: F24's `eventId` is only unique *within one team's
own event stream*, not globally — every delivery/shot lookup in this
package is scoped accordingly.

## Shot value (experimental)

Five pre-trained gradient-boosted models, bundled with the package, score
every shot in a match:

```bash
pip install -e ".[ml]"   # xgboost + scikit-learn + joblib
```

```python
from wa_setpieces.ml.shot_value import ShotValueModels, shot_value

models = ShotValueModels.load()          # loads once; reuse across matches
shots = shot_value(match.events, models)
# eventId, playerName, is_goal, set_piece_type, on_target_prob, xgot, psxg,
# situational_prob, outcome_class_0..3, shot_value (blended)
```

**Read `wa_setpieces/shot_value.py`'s module docstring before trusting this
for anything real.** The five models were trained elsewhere against a
feature schema this package has to reconstruct from Opta F24 qualifiers on
each shot event; some inputs (shot geometry, set-piece origin, assist,
left/right foot, goal-mouth placement) are confidently derived from
already-tested logic elsewhere in this package, but several situational
flags (big chance, one-on-one, fast break, scramble, header/volley) have no
reliable qualifier signal in the two real matches this was checked against
and default to `False` rather than a guessed-and-possibly-wrong qualifier
ID — that gap is documented, not hidden, but it does mean predictions are
degraded relative to the models' original training data.

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
    plot_set_piece_outcomes,  # shot map: every delivery, colored by outcome category
)

plot_delivery_map(
    delivery_locations(match.events, "corner"), title="Corner deliveries",
    subtitle="20 June 2026 · Delivery map", footer="Data: Opta", dark=False,  # or dark=True (default)
)
plot_dashboard(match.events, team_id, set_piece_type="corner")  # the "hero" figure
plot_set_piece_radar(corner_report(match.events, model=model))  # team A vs. team B, one glance
```

Every plotting function returns `(fig, ax)` (`plot_dashboard` returns just
`fig`, being multi-panel) for further customization, and takes `dark: bool
= True` -- the whole figure switches between a validated dark (navy) and
light (white) palette with that one argument, see
`wa_setpieces.viz.theme.get_palette`. Colors are assigned by the job they do —
a validated categorical palette for team identity (team-vs-team charts use
a fixed orange-then-blue pairing in both modes), a status pair for
success/fail, gold for goals, single-hue sequential ramps for magnitude,
and a diverging pair for signed quantities like xT added — not picked for
looks; see `wa_setpieces/viz/theme.py`. `subtitle` (a muted line under the
title) and `footer` (a small credit/source line, bottom-right) are
optional on every plot. See the
[gallery](https://waltzinganalytics.readthedocs.io/en/latest/gallery/index.html)
for all eleven plots (in both modes) with full source code.

## Command line

```bash
wa-setpieces match.json
wa-setpieces match.json --csv summary.csv
wa-setpieces match.json --xt   # also fit + print xT for this match (illustrative on one match)
```

## What counts as a set piece

| Type        | Detected on                              | Opta qualifierId |
|-------------|-------------------------------------------|-------------------|
| Penalty     | shot event (miss/post/saved/goal)          | 9                 |
| Kick-off    | pass event                                 | 279               |
| Free kick   | pass event (corners excluded)              | 5                 |
| Corner      | pass event                                 | 6                 |
| Throw-in    | pass event                                 | 107                |
| Goal kick   | pass event                                 | 124               |

These qualifier IDs are the standard Opta/Stats Perform F24 vocabulary and
were cross-checked against a real match export (see `tests/data/sample_match.json`
and `tests/test_filters.py`): tagged events line up with their expected pitch
location (corner arc, touchline, centre spot, six-yard line).

## Package layout

- `wa_setpieces.core.loader` — parse F24 JSON into a tidy `pandas.DataFrame`; `load_events_multi` stacks a whole season.
- `wa_setpieces.core.constants` — Opta typeId / qualifierId reference.
- `wa_setpieces.core.filters` — extract/tag each set-piece type.
- `wa_setpieces.core.metrics` — team/player counts, success rates, delivery locations.
- `wa_setpieces.core.chains` — link set pieces to the shots/goals they produced.
- `wa_setpieces.core.zones` — pitch thirds, channels and a configurable zone grid.
- `wa_setpieces.core.phases` — second-phase detection for corners/free kicks.
- `wa_setpieces.core.retention` — possession retention after any restart.
- `wa_setpieces.core.xt` — grid-based Expected Threat (xT), fit from data.
- `wa_setpieces.core.value` — set-piece added value: delivery xT + resulting shot quality + goals, blended.
- `wa_setpieces.core.outcomes` — per-delivery outcome classification (short corner, direct/second-phase shot, aerial duel, cleared, first/lost touch) for a shot-map scatter.
- `wa_setpieces.ml.shot_value` — five bundled pre-trained models (on-target probability, xGOT, post-shot xG, situational quality, outcome class) for a richer per-shot value score (optional `ml` extra; **experimental**, read the module docstring).
- `wa_setpieces.core.report` — `corner_report`/`free_kick_report`: everything above, merged into one table per team.
- `wa_setpieces.viz.plots` — mplsoccer/matplotlib plots: delivery maps, heatmaps, sonar, timeline, dashboard, radar (optional `viz` extra).
- `wa_setpieces.viz.theme` — the validated dark/light color palettes every plot draws from.
- `wa_setpieces.convert.corners` — batch-convert a directory of Opta F24 exports plus a match-list CSV into a flat corners table for tools that expect that schema (optional `convert` extra).
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

Docs are built with Sphinx (`pydata-sphinx-theme` + `sphinx-gallery`, the
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
