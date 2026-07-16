Changelog
=========

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
