Changelog
=========

0.5.1
-----

- Fixed the README's hero image not rendering on the PyPI project page --
  it used a repo-relative path, which GitHub resolves but PyPI's README
  renderer can't (no access to the repo tree); switched to an absolute
  URL and verified the whole README renders correctly through the actual
  PyPI renderer.
- Added ``Repository``, ``Changelog`` and ``Bug Tracker`` links to the
  PyPI project sidebar, alongside the existing ``Homepage``/``Documentation``.

0.5.0
-----

- **Fixed a real correctness bug**: F24's ``eventId`` is only unique
  *within one team's own event stream* (both teams number their events 1,
  2, 3, ... independently -- confirmed 1464 of 1613 rows in the sample
  match share an ``eventId`` with a same-numbered row from the other
  team). ``chains.link_set_piece_shots`` was resolving the assist-chain
  qualifier by ``eventId`` alone, which could silently attribute a shot to
  the wrong team's set piece; it's now scoped to ``(contestantId,
  eventId)``. ``viz.plot_second_phase`` had the same class of bug (an
  unscoped ``eventId`` lookup across all event types); it now searches
  only corner/free-kick deliveries and raises clearly on remaining
  ambiguity instead of silently picking the wrong one (new
  ``contestant_id`` parameter to disambiguate when needed).
- ``wa_setpieces.value``: set-piece added value -- ``delivery_xt_added +
  shot_value`` per delivery (the latter via a new ``XTModel.shot_value``
  using the fitted shot/goal probability grids), always summable (0, not
  NaN, when nothing happened). ``set_piece_added_value`` (per-delivery)
  and ``set_piece_value_summary`` (per-team).
- ``wa_setpieces.report``: ``set_piece_report`` / ``corner_report`` /
  ``free_kick_report`` merge attempts, success rate, second-phase rate,
  retention rate, and (with a model) added value and goals into one table
  per team -- previously five separate function calls.
- ``viz.plot_set_piece_radar``: two-team radar over a
  ``corner_report``/``free_kick_report``, built on ``mplsoccer.Radar``
  with per-axis auto-ranging (a raw count and a 0-1 rate need different
  scales, and a small-magnitude metric like avg added value needs a tight
  range or it flattens to invisible against a 0-1 default). Gallery grew
  from 10 examples to 12.
- ``viz.plot_xt_added_bars`` generalized with a ``value_col`` parameter so
  it works for ``added_value`` too, not just ``xt_added``.

0.4.0
-----

- Five new plots in ``wa_setpieces.viz``: ``plot_team_comparison``,
  ``plot_xt_added_bars``, ``plot_corner_sonar``, ``plot_match_timeline``,
  and ``plot_dashboard`` (a one-figure "report card" combining several of
  the others). Gallery grew from 5 examples to 10.
- ``wa_setpieces.theme``: a validated color palette (categorical, status,
  sequential blue/green, diverging blue/red) every plot now draws from,
  replacing ad hoc per-function color choices. Fixed a real bug along the
  way -- ``plot_team_comparison``/``plot_dashboard`` didn't guarantee which
  team got the first (blue) categorical slot, so "our team" could silently
  swap colors between panels.
- ``wa_setpieces.load_events_multi``: loads and stacks several F24 exports
  into one events DataFrame tagged with a ``matchId`` column, for
  match-independent aggregation (team/player counts, zone heatmaps,
  fitting ``XTModel`` across a season) -- documented as unsafe to feed
  directly into the per-match ``phases``/``retention`` window functions.
- Fixed ``plot_match_timeline``'s minute axis: Opta's ``timeMin`` already
  runs cumulatively across periods in F24 (period 2 continues from ~45,
  it doesn't reset to 0), so the previous per-period offset was double
  counting second-half events. Verified against the sample match.
- GitHub Actions: PyPI trusted-publisher release workflow and a pytest CI
  matrix (3.9/3.11/3.12).

0.3.0
-----

- ``wa_setpieces.viz``: mplsoccer-based pitch plots -- delivery maps,
  zone heatmaps, xT grids, and second-phase sequence plots (new ``viz``
  optional extra).
- ``wa_setpieces.zones.to_reference_frame``: mirrors one team's events
  onto a shared pitch frame, fixing a real bug where plotting both teams'
  raw coordinates together produced nonsensical positions (each event's
  x/y is in *that team's own* attacking direction).
- Docs rebuilt on ``pydata-sphinx-theme`` + ``sphinx-gallery`` (mplsoccer's
  stack): a runnable example gallery with embedded plots and DataFrame
  output, executed fresh on every docs build.

0.2.0
-----

- Second-phase detection for corners and free kicks (``wa_setpieces.phases``).
- Possession retention after any restart (``wa_setpieces.retention``).
- Pitch zones, thirds and channels (``wa_setpieces.zones``).
- Expected Threat (xT) engine, fit from data, with helpers for corner/free-kick
  delivery value (``wa_setpieces.xt``).
- CLI now prints second-phase, retention, and (with ``--xt``) xT sections.

0.1.0
-----

- Initial release: loader, extractors and metrics for penalties, kick-offs,
  free kicks, corners, throw-ins and goal kicks from Opta F24 event data.
- Set-piece-to-shot/goal chain linking via the assist-chain qualifier.
- ``wa-setpieces`` command-line tool.
