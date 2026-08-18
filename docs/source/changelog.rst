Changelog
=========

0.17.0
------

A larger batch: a column rename for clarity, CSV/Excel export, and five
new analyses (opponent scouting, penalty placement, long-throw
specialists, rolling defensive form) wired into the flagship pipeline.

- **Breaking change**: ``delivery_outcomes``/``classify_delivery_outcome``/
  ``outcome_summary``'s ``category`` column and ``restart_routines``'s
  ``outcome_category`` column are both renamed to ``delivery_outcome``.
  Both classified the same underlying concept -- what happened to one
  delivery -- under two different names, neither of which read distinctly
  from the raw pass/shot success ``outcome`` flag they sit next to in the
  same tables. No deprecation alias: these are new enough (0.6.0 and
  0.12.0 respectively) that a silent rename is preferable to carrying two
  names forward.
- **New**: ``save_table``/``save_tables`` -- save any table this package
  produces to CSV or Excel, chosen by file extension. Excel needs the new
  optional ``xlsx`` extra (openpyxl).
- **New**: ``opponent_scouting_report_html`` -- pre-match scouting report
  on how an opponent *defends* a set-piece type (conceded routines/zones,
  aerial-duel record), the conceding-side mirror of ``corner_report_html``.
- **New**: ``core.penalties`` -- ``penalty_placement_detail``/
  ``penalty_taker_summary``: per-penalty result and placement zone in the
  goal frame, per-taker conversion rate. Extracted the underlying
  goal-mouth placement geometry out of ``ml.shot_value`` into a new
  ``core.placement`` module (pure qualifier geometry, no model
  dependency) so it doesn't need the optional ``ml`` extra;
  ``ml.shot_value`` re-exports it as ``_goal_placement`` for backward
  compatibility.
- **New**: ``core.routines.long_throw_taker_summary``/
  ``long_throw_second_phases`` -- per-player long-throw usage/threat
  created, and event-sequence-based flick-on/knockdown detection
  restricted to throws that actually travel far enough to threaten (the
  one throw-in pattern that plays like a corner).
- **New**: ``SeasonDataset.rolling_defensive_summary`` -- the conceding-side
  mirror of ``rolling_summary``. Also documented ``rolling_summary``'s
  existing match-order caveat on both methods: there's no date field in
  the loaded schema, so "rolling" only means something if matches were
  supplied to ``from_sources`` already in chronological order.
- ``run_workflow``/``SetPieceWorkflow`` gained ``defensive_routine_summary``,
  ``defensive_zone_summary``, ``routine_clusters``,
  ``aerial_duel_team_summary``/``aerial_duel_player_summary``,
  ``penalty_placement``/``penalty_taker_summary`` and
  ``long_throw_taker_summary``/``long_throw_second_phases`` -- gated
  ``None`` where they don't apply to ``set_piece_type``, or where the
  optional ``ml`` extra isn't installed for ``routine_clusters``. No CLI
  changes needed: ``wa-setpieces workflow``/``report`` already collect
  every DataFrame field generically.

0.16.0
------

Finished the module-by-module review that produced 0.14.0/0.15.0, then
built out the corner-focused additions further: plots, gallery coverage,
and confirmation they already generalize to every set-piece type.

- **Fixed a real correctness bug**: ``convert.corners`` and
  ``providers.statsbomb`` both tagged in-swinging deliveries with
  qualifier 72, which is actually "Left Footed" in this package's
  Opta-derived schema (confirmed against the sample match: qualifier 72
  also appears on shot events, where swing direction is meaningless, and
  co-occurs with both real swing-direction qualifiers depending on which
  foot the taker used). The real in-swinger qualifier is 223, confirmed
  mutually exclusive with 224 (out-swinger) across every corner in the
  sample match. Every genuine in-swinger was previously going undetected
  unless the taker also happened to be left-footed (right label, wrong
  reason); a left-footed out-swinger was mislabeled "Inswinging". Added
  ``QUALIFIER_INSWINGER``/``QUALIFIER_OUTSWINGER`` to ``core.constants``
  as the shared, verified source.
- **Fixed a real correctness bug**: ``ml.shot_value.build_shot_features``
  re-looked-up each shot's raw event by ``(contestantId, eventId)``
  alone -- only unique within one match, since ``eventId`` resets every
  match -- so a shot in one match could silently inherit another match's
  qualifiers (foot preference, goal placement, ...) for the same pair.
  Reproduced directly and fixed by scoping to ``(matchId, contestantId,
  eventId)`` when ``matchId`` is present, the same pattern already
  applied to ``chains.link_set_piece_shots``/``value.set_piece_added_value``
  in 0.14.0. ``build_shot_features``/``shot_value`` now also carry
  ``matchId`` through to their output.
- **Fixed a real correctness bug**: ``providers.statsbomb.load_statsbomb_events``
  produced a columnless DataFrame for an empty export (same bug
  ``core.loader.load_events`` had for a zero-event match, fixed in
  0.14.0), failing ``schema.validate_events`` for the wrong reason.
- **New**: ``plot_routine_clusters``, ``plot_defensive_routine_bars`` and
  ``plot_aerial_duel_win_rate`` in ``wa_setpieces.viz.plots``, for
  ``cluster_routines``, ``defensive_routine_summary``/
  ``defensive_zone_summary`` and ``aerial_duel_summary`` respectively.
  Gallery grew from 17 examples to 20.
- Confirmed (no code change needed) that every 0.15.0 addition --
  ``delivery_technique``, ``post_target``, ``cluster_routines``,
  ``defensive_routine_summary``/``defensive_zone_summary``,
  ``aerial_duel_summary`` -- already works for every set-piece type, not
  just corners, since none of them hard-coded a corner-only restriction.
- Reviewed every remaining previously-unreviewed module
  (``ml.shot_value``, ``viz.plots``, ``viz.theme``, ``providers.statsbomb``,
  ``cli``) for correctness; ``viz.plots``, ``viz.theme`` and ``cli`` had
  no issues.

0.15.0
------

A batch of corner-focused additions, all built on already-existing pieces
rather than new inference:

- **New**: ``restart_routines`` gains ``delivery_technique``
  (``"inswinger"``/``"outswinger"``, from Opta qualifiers 223/224) and
  ``post_target`` (``"near_post"``/``"far_post"``/``"central"``, relative
  to which flank the restart was taken from) columns for corners and free
  kicks.
- **Fixed a real bug found along the way**: ``convert.corners``'s
  ``Q_INSWING`` was qualifier 72, which is actually "Left Footed" (also
  used, correctly, by ``ml.shot_value.QUALIFIER_LEFT_FOOTED``) -- confirmed
  against the sample match, where qualifier 72 also appears on shot
  events (where swing direction is meaningless) and co-occurs with both
  the real in-swing and out-swing qualifiers depending on which foot the
  taker used. Every genuine in-swinger was going undetected unless the
  taker also happened to be left-footed, and a left-footed player's
  out-swinger was mislabeled "Inswinging". The real in-swinger qualifier
  is 223 (confirmed mutually exclusive with 224 across every corner in
  the sample match), now shared as ``core.constants.QUALIFIER_INSWINGER``.
- **New**: ``cluster_routines`` -- k-means over delivery geometry as a
  data-driven alternative to ``routine_type``'s fixed rule-based taxonomy,
  surfacing whatever patterns a team actually repeats. Optional ``ml``
  extra (scikit-learn); ``cluster_summary`` rolls it up per cluster.
- **New**: ``defending.defensive_routine_summary`` /
  ``defensive_zone_summary`` -- flip ``restart_routines``'s attacking
  perspective to "which routines/zones is this team's defending most
  exposed to", e.g. conceding disproportionately from near-post
  inswingers.
- **New**: ``outcomes.classify_delivery_outcome`` identifies the winner of
  each ``aerial_duel`` delivery from the raw Opta Aerial event's own
  outcome flag (confirmed as a matched winner/loser pair per duel);
  ``aerial_duel_summary`` rolls that up into per-team win rate and
  per-player wins.
- **New**: ``corner_report_html`` -- a ready-to-view HTML scouting report
  for corners (team report, rating, outcome breakdown, routine mix, plus
  a delivery map and outcome shot map when the ``viz`` extra is
  installed), assembled from already-existing tables via the existing
  ``render_html_report``.
- **New**: ``delivery_clip_windows`` -- clip in/out timestamp windows (in
  match-clock seconds) for every delivery of any set-piece type, for
  handing off to video-clipping tools.

0.14.0
------

A code-review pass through every ``core`` module, working module by module in
dependency order. Nine real correctness bugs found and fixed, most verified
against the bundled sample match or a targeted synthetic reproduction:

- **Fixed a real correctness bug**: ``core.xt.XTModel.fit``'s value
  recurrence computed ``move_probability`` from *all* pass/take-on attempts
  (success or fail) but normalized the zone-to-zone transition matrix only
  over *successful* transitions (each row forced to sum to 1). Multiplying
  the two together silently assumed every attempted pass succeeds and lands
  like the successful ones did, discarding the value of a failed pass (a
  turnover, worth 0) -- a cell with a 100% pass-completion rate and one with
  10% got identical xT as long as both sent their (rare, for the second)
  successful passes to the same destination. The transition matrix is now
  normalized by total move attempts, matching ``move_probability``'s own
  denominator, so rows sum to the cell's actual pass-success rate.
- **Fixed a real correctness bug**: several functions indexed shots or
  deliveries by ``(contestantId, eventId)`` alone -- safe within one match,
  but ``eventId`` numbering restarts every match, so a season-combined
  frame (``matchId`` present) could silently attribute a goal or shot to a
  set piece actually taken in a *different* match that happened to reuse
  the same ``eventId`` for that team. Fixed in
  ``chains.link_set_piece_shots`` and ``value.set_piece_added_value`` by
  scoping the lookup to ``(matchId, contestantId, eventId)`` when
  ``matchId`` is present; ``metrics.delivery_locations`` and
  ``link_set_piece_shots`` now also carry ``matchId`` through to their
  output so callers can key on it.
- **Fixed a real correctness bug**: ``retention.retention_detail`` looked
  ahead for the next touch by filtering on ``periodId`` alone, which
  repeats every match, so a season-combined frame could pick up an
  unrelated later match's event as if it followed the current delivery --
  reproduced directly (a throw-in with no real follow-up in its own match
  was misreported as lost possession, using a later match's kickoff).
  Unlike ``phases.py``, which already guards the analogous risk with a
  2-team check, ``retention.py`` had no guard at all; it now raises a clear
  error instead of silently corrupting results. The existing internal
  caller (``routines.restart_routines``) was already unaffected, since it
  splits by ``matchId`` before calling in.
- **Fixed a real correctness bug**: ``zones.add_thirds``/``add_channels``
  returned ``NaN`` for the out-of-play events just beyond the nominal
  0-100 pitch boundary that Opta records and ``core.schema`` explicitly
  tolerates (-5..105) -- 26 and 100 rows respectively on the bundled
  sample match, mostly throw-ins, corners and clearances near the
  boundary lines. ``x``/``y`` are now clipped to 0-100 before binning,
  matching how ``zone_id``/``add_zone_grid`` already clamp.
- **Fixed a real correctness bug**: ``routines.py`` defined its own
  private third/channel helpers duplicating ``zones.add_thirds``/
  ``add_channels``, but with different bin edges *and* the opposite
  left/right direction (low ``y`` was "right" in ``routines.py``,
  "left_wide" in ``zones.py``) -- the same delivery could get
  contradictory flank labels depending on which function was called.
  ``routines.py`` now reuses ``zones.py``'s canonical helpers directly.
- **Fixed a real correctness bug**: ``core.loader.load_events`` produced a
  columnless (not just empty) DataFrame for a match with zero recorded
  events, failing ``schema.validate_events`` for the wrong reason.
  Sorting also broke ties within the same rounded
  ``periodId``/``timeMin``/``timeSec`` by ``eventId``, which is only
  unique within one team's own stream -- not a valid cross-team ordering
  key -- when the already-captured sub-second ``timeStamp`` field was
  available and unused; using it corrected one delivery's outcome
  classification in the sample match (``aerial_duel`` -> ``first_touch_lost``,
  verified by hand against the real timestamps).
- **Fixed a real bug**: ``run_workflow`` forwarded ``model`` straight
  through to ``set_piece_report`` regardless of ``set_piece_type``, which
  raises for anything other than corner/free-kick -- unlike every other
  model-dependent field in the same function, which already no-ops
  instead of crashing. A caller fitting one ``XTModel`` and looping
  ``run_workflow`` over all six set-piece types would crash on the first
  non-phase type.
- **Fixed a real bug**: ``outcomes.classify_delivery_outcome``'s
  ``no_action`` branch fell back with ``value or default``, which treats
  any falsy qualifier value -- including a genuine end position of 0.0,
  right on the touchline/byline -- as if it were missing.
- Hardened ``tests/test_filters.py``'s free-kick/corner disjointness check
  to compare on the globally-unique ``id`` column instead of the
  per-team-scoped ``eventId``, which could theoretically mask or spuriously
  flag a collision between two different teams' events.
- Every fix above has a regression test reproducing the original bug.

0.13.0
------

- Added the structured ``RoutineAnalysis`` bundle: restart detail, routine
  summary, team tactical profiles, taker profiles and target matrices.
- Added metric distance, delivery angle, verticality, destination zones,
  hierarchical outcomes and stable tactical pattern keys.
- Added team routine diversity, concentration/predictability, preferred
  patterns, shot/goal rates and taker-specific routine preferences.
- Made routine analysis safe on multi-match frames by isolating temporal and
  event-link calculations within each ``matchId``.

0.12.0
------

- Added ``restart_routines`` and ``routine_summary`` for corners, free kicks,
  throw-ins, penalties, goal kicks and kick-offs. Every restart now carries
  distance, progression, direction, side, start/end thirds, start/target
  channels, retention, shots, goals and a type-specific routine classification.
- Added ``all_routine_summaries`` for a complete routine inventory and included
  detailed and aggregate routine tables in ``run_workflow`` and generated reports.

0.11.0
------

- Added a validated provider-neutral event schema and capability discovery.
- Added ``SeasonDataset`` for match-safe season aggregation and rolling form.
- Added defensive set-piece summaries, ratings, and first-contact attribution.
- Added full xT model persistence, metadata, and held-out Brier evaluation.
- Added self-contained HTML reports and expanded CLI subcommands for summaries,
  workflows, reports, model training, providers, and structured exports.
- Added Python 3.13, coverage, wheel-install and lint checks to CI.

0.10.0
------

- **New**: ``wa_setpieces.core.rating`` -- benchmarked 0-100 team/player
  "how good" scores. Each metric in a report is z-scored against the
  sample it's given (50 = that sample's own average, +/-1 SD =~ +/-15
  points, clipped to [0, 100]) then combined into a composite ``rating``.
  ``team_rating()`` works on any ``set_piece_report``/``corner_report``/
  ``free_kick_report`` table. ``player_rating()`` splits into a delivery
  score (taker quality, from ``set_piece_added_value``) and a finishing
  score (shooter quality, from the assist-chain shot link and
  ``XTModel.shot_value``), merged so a pure taker or pure finisher is
  rated on the component they actually have. Always benchmark against a
  full season/competition, not one match -- see the module docstring.
- **New**: ``wa_setpieces.providers`` -- adapters that convert other
  providers' event feeds into the same internal frame
  ``wa_setpieces.core.loader.load_events`` produces from Opta F24, so
  every other module works unchanged regardless of source.
  ``wa_setpieces.providers.statsbomb.load_statsbomb_events`` (also
  exported as ``wa_setpieces.load_statsbomb_events``) converts a
  StatsBomb open-data events export: set-piece detection, the
  assist-chain shot link (``key_pass_id``), retention, xT, added value
  and the new rating module are all faithfully mapped; one narrow
  second-phase-timing edge case is a documented approximation (StatsBomb
  has no event type equivalent to Opta's distinct "ball went out of
  play" event). Impect is not supported -- it's a closed feed with no
  public schema to build and verify an adapter against.
- **New**: ``plot_rating_benchmark`` in ``wa_setpieces.viz.plots`` --
  horizontal benchmark chart for a ``team_rating``/``player_rating``
  table, diverging from the sample-average baseline of 50.
- **New**: ``wa_setpieces.core.workflow.run_workflow`` (also exported as
  ``wa_setpieces.run_workflow``) -- runs this package's full pipeline for
  one set-piece type in a single call (extraction, team/player counts,
  second phases, retention, added value, report, team/player rating) and
  returns every table in one ``SetPieceWorkflow``. Computes nothing new;
  it's a convenience wrapper around the existing functions for when you
  want the whole chain without wiring five calls together yourself.

0.9.0
-----

- **Breaking: the package is now organized into subpackages** instead of
  ~20 flat modules directly under ``wa_setpieces``. Import paths change;
  the top-level API (``from wa_setpieces import load_events, XTModel, ...``)
  is unaffected.

  - ``wa_setpieces.core`` -- loading, extraction, metrics, chains, phases,
    retention, xT, added-value, outcomes, report, constants. No extra
    dependencies; imported eagerly (e.g. ``wa_setpieces.xt`` moved to
    ``wa_setpieces.core.xt``, ``wa_setpieces.constants`` to
    ``wa_setpieces.core.constants``, and so on for every other module that
    used to sit directly under ``wa_setpieces``).
  - ``wa_setpieces.ml`` -- ``wa_setpieces.shot_value`` moved to
    ``wa_setpieces.ml.shot_value``; the bundled ``.pkl`` models moved with
    it to ``wa_setpieces/ml/models/`` (``ml`` extra unchanged).
  - ``wa_setpieces.viz`` -- ``wa_setpieces.viz`` (the plotting module) moved
    to ``wa_setpieces.viz.plots``; ``wa_setpieces.theme`` moved to
    ``wa_setpieces.viz.theme``. ``wa_setpieces.viz.theme`` still imports
    without mplsoccer installed (only matplotlib) -- the ``viz`` package's
    ``__init__`` does not eagerly import ``plots``, so pulling in the
    palette doesn't pull in the heavier plotting dependency.
  - ``wa_setpieces.convert`` -- new. See below.

- **New**: ``wa_setpieces.convert.corners`` (optional ``convert`` extra --
  pyarrow) batch-converts a directory of Opta F24 match JSON exports, plus
  a companion match-list CSV, into a flat "corners" table (one row per
  corner delivery, with any shot it produced linked by a time/possession
  heuristic) matching the schema external tools already consume. Also
  available as the ``wa-setpieces-convert-corners`` console script.

0.8.0
-----

- **New (experimental)** ``wa_setpieces.ml.shot_value``: five pre-trained
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
  validated palettes in ``wa_setpieces.viz.theme`` (``get_palette(dark)``)
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

- ``wa_setpieces.core.outcomes``: per-delivery outcome classification for
  corners and free kicks -- ``short_corner``, ``direct_shot``,
  ``second_phase_shot``, ``aerial_duel`` ("50/50", ``typeId`` 44),
  ``cleared``, ``first_touch_won``, ``first_touch_lost`` or ``no_action``.
  ``delivery_outcomes`` (per-delivery) and ``outcome_summary`` (per-team
  rollup). Built on ``wa_setpieces.core.phases``, which now also records
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
- ``wa_setpieces.core.value``: set-piece added value -- ``delivery_xt_added +
  shot_value`` per delivery (the latter via a new ``XTModel.shot_value``
  using the fitted shot/goal probability grids), always summable (0, not
  NaN, when nothing happened). ``set_piece_added_value`` (per-delivery)
  and ``set_piece_value_summary`` (per-team).
- ``wa_setpieces.core.report``: ``set_piece_report`` / ``corner_report`` /
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
- ``wa_setpieces.viz.theme``: a validated color palette (categorical, status,
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
- ``wa_setpieces.core.zones.to_reference_frame``: mirrors one team's events
  onto a shared pitch frame, fixing a real bug where plotting both teams'
  raw coordinates together produced nonsensical positions (each event's
  x/y is in *that team's own* attacking direction).
- Docs rebuilt on ``pydata-sphinx-theme`` + ``sphinx-gallery`` (mplsoccer's
  stack): a runnable example gallery with embedded plots and DataFrame
  output, executed fresh on every docs build.

0.2.0
-----

- Second-phase detection for corners and free kicks (``wa_setpieces.core.phases``).
- Possession retention after any restart (``wa_setpieces.core.retention``).
- Pitch zones, thirds and channels (``wa_setpieces.core.zones``).
- Expected Threat (xT) engine, fit from data, with helpers for corner/free-kick
  delivery value (``wa_setpieces.core.xt``).
- CLI now prints second-phase, retention, and (with ``--xt``) xT sections.

0.1.0
-----

- Initial release: loader, extractors and metrics for penalties, kick-offs,
  free kicks, corners, throw-ins and goal kicks from Opta F24 event data.
- Set-piece-to-shot/goal chain linking via the assist-chain qualifier.
- ``wa-setpieces`` command-line tool.
