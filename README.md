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
  <img src="docs/source/_static/hero_corners.png" alt="Corner delivery map drawn with mplsoccer" width="640">
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

## Second phases, xT, zones and retention

```python
from wa_setpieces import (
    second_phases, second_phase_summary,   # corner/free-kick second-phase shots
    retention_detail, retention_rate,      # possession retained N seconds later
    add_thirds, add_channels, add_zone_grid,  # pitch location tagging
    XTModel, set_piece_delivery_xt, set_piece_xt_summary,  # Expected Threat
)

second_phases(match.events, "corner")           # per-corner: cleared / first-phase shot / second-phase shot
second_phase_summary(match.events, "free_kick") # per-team roll-up

retention_rate(match.events, "corner")          # per-team: % of corners where the ball is retained ~8s later

tagged = add_thirds(match.events)               # defensive_third / middle_third / attacking_third
tagged = add_channels(tagged, n=5)              # wide / half-space / central

model = XTModel.fit(match.events)               # fit an xT grid (fit on many matches for real use!)
set_piece_xt_summary(match.events, "corner", model)  # total/average xT added per team
```

All four are **derived heuristics**, not raw Opta fields — see
`docs/source/advanced.rst` (or the hosted docs) for the exact assumptions
and tunable thresholds behind each one.

## Plots

```bash
pip install -e ".[viz]"   # matplotlib + mplsoccer
```

```python
from wa_setpieces.viz import plot_delivery_map, plot_zone_heatmap, plot_xt_grid, plot_second_phase

plot_delivery_map(delivery_locations(match.events, "corner"), title="Corner deliveries")
plot_zone_heatmap(extract_corners(match.events), title="Corner origin zones")
plot_xt_grid(model)
plot_second_phase(match.events, delivery_event_id=610)  # numbered touches through a phase
```

Every plotting function returns `(fig, ax)` for further customization. See
the [gallery](https://waltzinganalytics.readthedocs.io/en/latest/gallery/index.html)
for all of these with full source code.

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

- `wa_setpieces.loader` — parse F24 JSON into a tidy `pandas.DataFrame`.
- `wa_setpieces.constants` — Opta typeId / qualifierId reference.
- `wa_setpieces.filters` — extract/tag each set-piece type.
- `wa_setpieces.metrics` — team/player counts, success rates, delivery locations.
- `wa_setpieces.chains` — link set pieces to the shots/goals they produced.
- `wa_setpieces.zones` — pitch thirds, channels and a configurable zone grid.
- `wa_setpieces.phases` — second-phase detection for corners/free kicks.
- `wa_setpieces.retention` — possession retention after any restart.
- `wa_setpieces.xt` — grid-based Expected Threat (xT), fit from data.
- `wa_setpieces.viz` — mplsoccer-based pitch plots (optional `viz` extra).
- `wa_setpieces.cli` — `wa-setpieces` command-line tool.

## Development

```bash
pip install -e ".[dev]"
pytest
```

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
