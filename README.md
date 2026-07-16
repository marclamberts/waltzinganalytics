# opta-setpieces

Set-piece metrics for football (soccer) matches from **Opta / Stats Perform F24**
event-feed JSON exports: penalties, kick-offs, free kicks, corners,
throw-ins and goal kicks.

Given a raw F24 match file, this package tags every set-piece restart,
aggregates attempts/success rates by team and player, tracks pass end
locations for delivery maps, and links each set piece to the shot or goal
it produced (via Opta's assist-chain qualifier).

Full documentation: https://waltzinganalytics.readthedocs.io

## Install

```bash
pip install -e .
```

## Quickstart

```python
from opta_setpieces import load_events, set_piece_summary

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

## Command line

```bash
opta-setpieces match.json
opta-setpieces match.json --csv summary.csv
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

- `opta_setpieces.loader` — parse F24 JSON into a tidy `pandas.DataFrame`.
- `opta_setpieces.constants` — Opta typeId / qualifierId reference.
- `opta_setpieces.filters` — extract/tag each set-piece type.
- `opta_setpieces.metrics` — team/player counts, success rates, delivery locations.
- `opta_setpieces.chains` — link set pieces to the shots/goals they produced.
- `opta_setpieces.cli` — `opta-setpieces` command-line tool.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Docs

Docs are built with Sphinx and hosted on Read the Docs (`.readthedocs.yaml`
at the repo root). To build locally:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/_build/html
```

## License

MIT
