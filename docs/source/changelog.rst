Changelog
=========

0.3.0
-----

- ``opta_setpieces.viz``: mplsoccer-based pitch plots -- delivery maps,
  zone heatmaps, xT grids, and second-phase sequence plots (new ``viz``
  optional extra).
- ``opta_setpieces.zones.to_reference_frame``: mirrors one team's events
  onto a shared pitch frame, fixing a real bug where plotting both teams'
  raw coordinates together produced nonsensical positions (each event's
  x/y is in *that team's own* attacking direction).
- Docs rebuilt on ``pydata-sphinx-theme`` + ``sphinx-gallery`` (mplsoccer's
  stack): a runnable example gallery with embedded plots and DataFrame
  output, executed fresh on every docs build.

0.2.0
-----

- Second-phase detection for corners and free kicks (``opta_setpieces.phases``).
- Possession retention after any restart (``opta_setpieces.retention``).
- Pitch zones, thirds and channels (``opta_setpieces.zones``).
- Expected Threat (xT) engine, fit from data, with helpers for corner/free-kick
  delivery value (``opta_setpieces.xt``).
- CLI now prints second-phase, retention, and (with ``--xt``) xT sections.

0.1.0
-----

- Initial release: loader, extractors and metrics for penalties, kick-offs,
  free kicks, corners, throw-ins and goal kicks from Opta F24 event data.
- Set-piece-to-shot/goal chain linking via the assist-chain qualifier.
- ``opta-setpieces`` command-line tool.
