Changelog
=========

0.8.0
-----

- **New (experimental)** ``wa_setpieces.shot_value``: five pre-trained
  gradient-boosted models (xgboost + isotonic calibration), bundled with
  the package (``wa_setpieces/models/*.pkl``, new ``ml`` optional extra --
  xgboost, scikit-learn, joblib), score every shot in a match:
  ``on_target_prob``, ``xgot`` (xG On Target), ``psxg`` (Post-Shot xG),
  ``situational_prob``, a 4-class outcome distribution, and a blended
  ``shot_value`` column. ``build_shot_features()`` reconstructs the
  models' training feature schema from Opta F24 qualifiers, reusing
  already-tested logic elsewhere in this package (``chains.link_set_piece_shots``,
  ``phases.second_phases``, the validated ``QUALIFIER_ASSIST`` constant)
  wherever possible. **Read the module's docstring before trusting the
  output**: several situational flags (big chance, one-on-one, fast
  break, scramble, header/volley) have no reliable qualifier signal in
  the real match data this was checked against and default to ``False``
  rather than a guessed-and-possibly-wrong mapping -- documented
  explicitly as a known limitation, not silently assumed correct.
- **Fixed a real bug found by the new test suite**: ``bool(float('nan'))``
  is ``True`` in Python, so the first implementation of the qualifier-flag
  read (``bool(raw_event.get("q_20"))``) treated *every* absent qualifier
  column as present -- every shot came out "assisted" and often "both
  right- and left-footed" regardless of the real data. Fixed with a
  ``pd.notna()``-aware helper (``_qualifier_flag``); verified against the
  sample match that assisted/unassisted and left/right-foot splits are
  now correctly mutually exclusive and match the real qualifier data.
- Gallery grew from 14 examples to 15.

0.7.0
-----

- **Restyled the whole plotting suite and added light/dark mode.** Every
  function in ``wa_setpieces.viz`` now takes ``dark: bool = True`` --
  the pitch, chart chrome and team colors all switch between two
  validated palettes in ``wa_setpieces.theme`` (``get_palette(dark)``)
  with that one argument. Both a navy dark surface (``#0d1117``) and a
  clean white light surface (``#ffffff``) pass the full colorblind-safety
  and contrast validator, run against their own chart surface.
- Two-team charts (``plot_team_comparison``, ``plot_match_timeline``,
  ``plot_dashboard``, ``plot_set_piece_radar``) now use a fixed,
  validated orange-then-blue ``team_colors`` pairing instead of the
  general 8-slot categorical order's blue/green -- the first team is
  always orange, the second always blue, consistent across a whole
  report. This is a separate, standalone-validated 2-color convention;
  the general ``CATEGORICAL`` order (used by e.g.
  ``plot_set_piece_outcomes``'s 8 outcome categories) is unchanged.
- New fixed ``theme.GOLD`` accent for goals, used for the "Goal" ring in
  ``plot_set_piece_outcomes`` and the second-phase-shot highlight in
  ``plot_second_phase`` (previously the categorical yellow slot and a
  plain white ring, respectively) -- distinct from both team colors and
  the good/critical status colors, never reused for series identity.
- Every plotting function gained optional ``subtitle`` (a muted line
  under the title) and ``footer`` (a small credit/source line,
  bottom-right of the figure) parameters. Neither is set by default --
  a source credit belongs to whoever is publishing the chart.
- Fixed a legend/bar overlap in ``plot_team_comparison``: the default
  ``loc="lower right"`` legend clipped into the throw-in bars (the
  longest, at the bottom of the chart, in the sample match); moved to
  ``upper right``, verified against the sample match with no collision.
- ``theme.Palette`` and ``theme.get_palette(dark)`` are the new
  recommended API; the old module-level constants (``theme.SURFACE``,
  ``theme.CATEGORICAL``, ...) still work, pinned to the dark palette.
- Gallery grew from 13 examples to 14, with a new light/dark
  side-by-side example.

0.6.0
-----

- ``wa_setpieces.outcomes``: per-delivery outcome classification for
  corners and free kicks -- ``short_corner``, ``direct_shot``,
  ``second_phase_shot``, ``aerial_duel`` ("50/50", ``typeId`` 44),
  ``cleared``, ``first_touch_won``, ``first_touch_lost`` or ``no_action``.
  ``delivery_outcomes`` (per-delivery) and ``outcome_summary`` (per-team
  rollup). Built on ``wa_setpieces.phases``, which now also records
  whether a set piece produced a direct shot on the delivery itself
  (``PhaseResult.direct_shot``/``direct_shot_event_id``/``direct_shot_is_goal``)
  -- previously that information was discarded once a direct shot was
  detected.
- ``viz.plot_set_piece_outcomes``: a colored-scatter shot map, one point
  per delivery at the outcome location, colored by category, with a ring
  around goals. Gallery grew from 12 examples to 13.
- Fixed a threshold contradiction in the short-corner heuristic: the
  original ``max_distance=15.0`` *and* ``max_end_x=85.0`` conditions were
  nearly mutually exclusive given corners start at x≈99.5 (at most ~0.5
  units of overlap, eliminated entirely by any y-component), so almost no
  short corner could ever satisfy both. Dropped the end-x condition and
  lowered the distance threshold to a more realistic 12.0; verified this
  correctly reclassifies a real short corner in the sample match that the
  old thresholds mislabeled as a lost first touch.

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
