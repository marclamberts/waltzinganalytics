Changelog
=========

0.31.4
------

- Added a work-in-progress notice to the top of the docs homepage
  (:doc:`index`) and the README: this package is under active
  development with heavy updates expected in the near future, and a
  contact address (marc@waltzinganalytics.com) for feedback or trouble.
  No functional changes. Docs build clean.

0.31.3
------

Doc-accuracy pass, prompted by the user asking to check every page of the
published docs for stale or invalid text after 0.31.1/0.31.2's loading-API
changes. Read every hand-written page (``index``, ``installation``,
``quickstart``, ``categories``, ``by_metric``, ``by_phase``, ``by_report``,
``by_routine``, ``value_models``) against the current code -- every
function/class reference, code example and CLI invocation checked
individually against its actual signature or ``argparse`` definition.

- **Fixed**: the ``wa-setpieces`` CLI's own ``--help`` text (``summary``/
  ``workflow``/``report``'s ``input`` argument, and ``season``'s
  ``inputs`` argument) still described the pre-0.31.1 behaviour --
  "``*.json for opta/statsbomb, *.csv for impect``" and "``*.json/*.csv
  per --provider``" -- directly contradicting how ``load_matches``
  actually resolves a folder's files today (every ``*.json`` and
  ``*.csv`` file, regardless of provider). The underlying loading code
  was already correct; only the help strings were stale. Updated both to
  describe the real behaviour.
- All nine hand-written docs pages otherwise verified accurate as-is:
  every ``:func:``/``:class:`` reference resolves to a real symbol,
  every code example matches its function's real signature, every CLI
  example matches ``cli.py``'s actual argument definitions. No changes
  needed there.
- 382 tests still passing, docs build clean.

0.31.2
------

Follow-up to 0.31.1, prompted directly by user feedback: "every provider
can be json or csv." 0.31.1 made the ``type="season"`` folder *scan*
extension-agnostic; this release makes each provider's own *parser*
extension-agnostic too, so a single ``type="match"`` file works either
way regardless of which format that provider natively ships as.

- **Changed**: :func:`~wa_setpieces.load_events` (Opta) now accepts a
  ``.csv`` path in addition to native ``.json`` -- read as-is, since a
  ``.csv`` here always means a previously-exported round-trip of this
  same internal events shape (e.g. ``match.events.to_csv(...)`` from an
  earlier run), never a different Opta feed format. ``match_details`` is
  ``{}`` for a CSV source, since a CSV round-trip carries no
  ``matchDetails`` block.
- **Changed**: :func:`wa_setpieces.providers.statsbomb.load_statsbomb_events`
  now accepts a ``.csv`` path the same way -- StatsBomb open data itself
  is JSON-only, so a ``.csv`` source always means "already converted,"
  read directly rather than run through the StatsBomb-specific event
  conversion.
- **Changed**: :func:`wa_setpieces.providers.impect.load_impect_events`
  now accepts a ``.json`` path in addition to native ``.csv`` -- a
  JSON-encoded version of the same raw IMPECT record shape (e.g.
  ``raw_df.to_json(orient="records")``), handled identically to the CSV
  path from that point on.
- Verified round-trip safe against real data before writing any of the
  above, not assumed: an Opta match's events written to CSV and reread
  produce identical :func:`~wa_setpieces.delivery_locations`/
  :func:`~wa_setpieces.set_piece_summary` output to the original
  JSON-parsed frame (despite some ``q_<id>`` columns relabeling
  ``object`` -> ``float64`` through the round-trip -- harmless, since
  every value that matters goes through :func:`pandas.to_numeric`
  downstream regardless); a real IMPECT export's raw records written to
  JSON and reread produce identical output to the CSV-sourced version
  (only an unused passthrough ``id`` column's dtype label differs).
- Docstrings (module-level and per-function, in ``core/loader.py``,
  ``providers/statsbomb.py`` and ``providers/impect.py``) and the
  :doc:`installation` page updated to describe the round-trip
  acceptance.
- 4 new tests (382 total): Opta CSV round-trip via both
  :func:`~wa_setpieces.load_events` and :func:`~wa_setpieces.load_matches`,
  StatsBomb CSV round-trip, IMPECT JSON round-trip. Docs build clean.

0.31.1
------

Follow-up to 0.31.0, prompted directly by user feedback on the new
``type=`` parameter: "all load matches can be any of them, all seasons
can be any of them, and they all can be csv or json."

- **Changed**: :func:`~wa_setpieces.load_matches` no longer gates a
  ``type="season"`` folder scan to one fixed extension per provider
  (``*.json`` for Opta/StatsBomb, ``*.csv`` for IMPECT). It now scans
  for **every** ``*.json`` and ``*.csv`` file together, regardless of
  ``provider`` -- the file extension never decides which files are even
  considered; ``provider`` alone decides whether a given file's
  *content* parses. A folder can mix extensions freely; anything that
  doesn't parse under the chosen provider is skipped with the same
  :class:`UserWarning` mechanism 0.31.0 already added for
  ``matches.json``-style sidecar files, not filtered out silently by
  extension up front.
- ``type="match"`` was already extension-agnostic (a single ``source``
  file was always handed straight to the provider's loader, whatever
  its extension) -- this release makes ``type="season"`` consistent
  with that, rather than changing ``type="match"`` itself.
- Docstrings and the :doc:`installation` page updated to describe the
  provider/extension relationship accurately.
- 1 new test (378 total): a mixed-extension season folder where the
  wrong-provider file gets skipped, not excluded from the scan up
  front. Docs build clean.

0.31.0
------

Two changes prompted by actually running the new loading API against a
full real season, not synthetic test fixtures: an API redesign for
consistency, and a real bug the redesign's own verification run caught.

- **Changed**: :func:`~wa_setpieces.load_matches` gained an explicit
  ``type: str = "match"`` parameter (``"match"`` or ``"season"``,
  case-insensitive) instead of silently inferring "single file" versus
  "folder" from whether ``source`` happens to be a directory. Every call
  now has the same two keywords regardless of provider or scope --
  ``load_matches("match.json", provider="opta", type="match")``,
  ``load_matches("season/", provider="statsbomb", type="season")`` --
  and passing a directory with ``type="match"`` (or a file with
  ``type="season"``) raises ``ValueError`` instead of silently doing the
  other thing. This is a **breaking change** for any code relying on the
  old auto-detection with a directory ``source`` -- add
  ``type="season"`` explicitly.
- **Fixed a real bug**, caught while re-verifying the above against a
  real ~240-match StatsBomb season folder: the folder also contained a
  ``matches.json`` (StatsBomb's own match-list metadata file, not an
  events export) which matched the ``*.json`` glob and got parsed as if
  it were 242 events, silently corrupting the combined frame with
  garbage rows (``id``/``eventId`` empty, ``typeId`` 0) until
  ``validate_events`` rejected it several steps downstream with a
  confusing "column 'eventId' contains non-numeric values" error nowhere
  near the actual cause. Fixed at the source
  (:func:`~wa_setpieces.providers.statsbomb.load_statsbomb_events` now
  validates its input actually looks like an events list -- has ``id``
  and ``type`` fields -- before parsing it) and at the call site
  (:func:`~wa_setpieces.load_matches` catches a bad file per-source
  during a ``type="season"`` scan, skips it with a
  :class:`UserWarning` naming it and why, and keeps loading the rest of
  the folder, rather than either corrupting the frame or aborting over
  one bad file).
- The CLI is unaffected -- its own file-or-folder auto-detection on
  ``input``/``inputs`` is unchanged; it now resolves the explicit
  ``type=`` internally before calling :func:`load_matches`.
- ``examples/load_matches_demo.ipynb`` -- a new notebook exercising all
  three providers (Opta bundled sample, a real StatsBomb match, a real
  ~240-match StatsBomb season folder, a real 20-match IMPECT export)
  end to end, actually executed against real data rather than just
  written -- is what caught the ``matches.json`` bug above in the first
  place.
- Every ``provider=``/``type=`` example across :doc:`index`,
  :doc:`installation`, :doc:`quickstart` and the README updated to show
  both keywords explicitly and consistently.
- 7 new tests (377 total, up from 370): explicit ``type`` validation,
  the ``matches.json``-skip behavior, and the underlying
  ``providers.statsbomb`` input-shape check. Docs build clean.

0.30.2
------

Second follow-up to 0.30.0: 0.30.1 fixed the gallery, README and
index/quickstart; this sweep found the rest -- the six pick-one
reference pages (:doc:`categories`, :doc:`value_models`, :doc:`by_metric`,
:doc:`by_phase`, :doc:`by_routine`, :doc:`by_report`), which all still
showed ``events`` implicitly loaded via the old ``match.events`` pattern
in their code samples.

- All six reference pages now consistently assume ``events =
  load_matches(...)``, matching :doc:`quickstart`.
- Two runnable example scripts also swept: ``examples/analyse_opta.py``
  and its paired ``examples/analyse_opta.ipynb`` now use
  :func:`~wa_setpieces.load_matches` (neither used the ``matchDetails``
  block, so there was no reason to keep the lower-level function) --
  the notebook was actually re-executed, not just text-edited, so its
  saved outputs (including the now-present ``matchId`` column in the
  events preview) reflect what the new code really produces, not a
  stale cell result.
- ``examples/quickstart.py`` and ``examples/full_walkthrough.ipynb``
  were deliberately left on :func:`~wa_setpieces.load_events` -- both
  genuinely read ``match.match_details`` (kickoff status, final score),
  which :func:`~wa_setpieces.load_matches` doesn't provide, so
  :func:`~wa_setpieces.load_events` is the correct call there, not a
  leftover.
- Docs build clean (zero warnings), 370 tests unchanged -- text and
  example code only, no library behavior changed.

0.30.1
------

Follow-up to 0.30.0: made :func:`~wa_setpieces.load_matches` the
example code actually shows, not just a function that exists alongside
the old pattern.

- Every gallery example (all 39 scripts), the README, and the docs'
  ``index``/``quickstart`` pages now load with
  ``events = load_matches(DATA)`` instead of ``match = load_events(DATA)``
  / ``match.events`` -- the pattern the rest of this changelog has been
  telling people to prefer since 0.30.0, now actually followed
  everywhere it's demonstrated. :func:`~wa_setpieces.load_events`
  (returning the ``matchDetails`` block alongside events) is still
  documented as the lower-level alternative for when that block is
  actually needed.
- Caught and fixed two stale example outputs while touching this code,
  the same kind of drift found in the 0.29.1 docs review: the
  README's sample ``set_piece_summary()`` table showed a ``shots``
  column of 1 for two rows where a fresh run against the same sample
  match gives 0 throughout.
- No functional changes -- :func:`~wa_setpieces.load_events` and
  :func:`~wa_setpieces.core.loader.load_events_multi` are unchanged and
  still exported; this is example code and documentation only.
- Docs build clean (39/39 gallery scripts, zero warnings), 370 tests
  unchanged.

0.30.0
------

A unified, provider-based loading entry point plus a new IMPECT
converter -- built and verified against two real exports the user
provided (a StatsBomb open-data match and a 20-match IMPECT CSV, iteration
2128), not synthetic guesses at either schema.

- **Added**: :func:`~wa_setpieces.core.loader.load_matches` -- the one
  loading entry point for any provider (``provider="opta"`` default,
  ``"statsbomb"`` or ``"impect"``) and either a single match file or a
  whole folder of them (a season): ``load_matches("match.json")``,
  ``load_matches("season/", provider="statsbomb")``,
  ``load_matches("impect_export.csv", provider="impect")``. Always
  returns one combined events DataFrame with a ``matchId`` column, the
  same shape :func:`~wa_setpieces.core.loader.load_events_multi`
  produces, ready for :class:`~wa_setpieces.core.season.SeasonDataset`
  or any match-safe function in this package. Fails loudly (not
  silently) if two different files would resolve to the same
  ``matchId`` -- same safety net :func:`load_events_multi` already had.
- **Added**: :mod:`wa_setpieces.providers.impect` --
  :func:`~wa_setpieces.providers.impect.load_impect_events` converts an
  IMPECT CSV export into the same internal events shape every other
  provider produces. Verified against a real 20-match, ~53k-event
  export end to end -- :func:`~wa_setpieces.set_piece_summary`,
  :func:`~wa_setpieces.delivery_locations`,
  :func:`~wa_setpieces.retention_rate`,
  :func:`~wa_setpieces.core.phases.second_phases`,
  :func:`~wa_setpieces.core.chains.link_set_piece_shots` and
  :func:`~wa_setpieces.viz.plots.plot_delivery_map` all ran against the
  converted output and produced plausible results cross-checked against
  the raw export (e.g. a team's real corner count for one match matched
  exactly). See the module docstring for exactly what's mapped and what
  isn't, including two coordinate/timing conventions confirmed by
  inspecting the real export rather than assumed: ``adjCoordinates`` is
  already attacking-direction-normalized (raw ``coordinates`` flips sign
  at half-time; ``adjCoordinates`` doesn't), and each period's
  ``gameTime.gameTimeInSec`` restarts at a ``(periodId - 1) * 10000``
  offset.
- Two real bugs caught and fixed during that verification, not just
  polish: a `KeyError` when the optional ``setPiece.id``/
  ``setPiece.mainEvent`` columns are absent from a stripped export
  (assist-chain linking now degrades to "unavailable" instead of
  crashing), and 423 events with no ``squadId`` (video gaps, the final
  whistle, referee touches -- confirmed exhaustive against the reference
  export) getting a null ``eventId`` that
  :func:`~wa_setpieces.core.schema.validate_events` rejected outright --
  now dropped, since there's no meaningful team-scoped identity for a
  teamless event anyway.
- **Fixed a real bug in the CLI's own new duplicate-matchId check**,
  caught by running it against the real IMPECT export: the first
  version checked for duplicated ``matchId`` values across every *row*
  in the combined frame, which always fires since one match's ``matchId``
  legitimately repeats across all of that match's own event rows --
  fixed to compare each input's *set* of match IDs instead.
- **Fixed an unrelated, adjacent bug found while touching this same
  file**: ``wa_setpieces.__version__`` was a hardcoded string that had
  drifted to ``"0.18.3"`` while ``pyproject.toml`` was already at
  ``0.29.1`` -- now read from the installed package's own metadata via
  ``importlib.metadata``, a single source of truth that can't silently
  go stale again.
- The CLI's ``--provider`` choices gained ``impect`` everywhere they
  already had ``opta``/``statsbomb``; every command's file argument now
  also accepts a folder (loaded and combined the same way
  ``load_matches`` does).
- ``wa_setpieces.providers.statsbomb.load_statsbomb_events`` and the CLI
  are otherwise unchanged -- ``load_matches`` is a new entry point in
  front of them, not a rewrite.
- :doc:`index`, :doc:`installation`, :doc:`quickstart` and
  :doc:`by_report` updated for the new loading story.
- 20 new tests (370 total, up from 350) -- synthetic IMPECT fixtures
  in the test suite itself (small, fast, no dependency on the external
  files this feature was verified against), plus regression tests for
  both bugs above. Docs build clean, zero warnings.

0.29.1
------

Docs content review -- read every narrative page (``index``,
``installation``, ``quickstart``, ``categories``, ``value_models``,
``by_metric``, ``by_phase``, ``by_routine``, ``by_report``) end to end
and checked all four admonition boxes render correctly (they do). Found
and fixed three real inaccuracies, not just polish:

- **Fixed**: :doc:`quickstart`'s sample ``set_piece_summary()`` output
  table was stale and incomplete -- it showed a ``shots`` column of 1
  for two rows where the real output (re-run against the same sample
  match) is 0 throughout, and only showed one team's 5 rows out of the
  10 the function actually returns. Replaced with the current, complete
  output.
- **Fixed**: :doc:`categories`' penalty section claimed "six placement
  zones" -- :func:`~wa_setpieces.core.placement.goal_placement`'s own
  docstring and code both say a 3x3 grid (nine zones); confirmed against
  the source before fixing the doc, not the other way around.
- **Fixed**: :doc:`installation`'s "Not yet published to PyPI? Install
  from source instead" framing was stale -- the package has been on
  PyPI for many versions -- reworded to state the actual reason to
  install from source (unreleased changes, contributing).
- Two accuracy improvements, not corrections: :doc:`by_phase`'s
  Outcomes section now also points to
  :func:`~wa_setpieces.viz.plots.plot_outcome_flow` (built on exactly
  the data that section documents, previously unmentioned there); and
  :doc:`value_models`'s Added Value section now lists the five
  value-focused charts built on it
  (:func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow`,
  ``plot_value_waterfall``, ``plot_value_distribution``,
  ``plot_value_ridgeline``, ``plot_value_boxplot``) instead of none of
  them.
- Docs build clean (zero warnings, ``-W --keep-going``), 350 tests
  still passing (unchanged -- doc content only, no code behavior
  touched).

0.29.0
------

Three more new chart forms -- a delivery combination network, a
histogram, and a box plot -- none of which existed anywhere in the
module before.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_delivery_combination_network`
  -- a node-link graph of which player takes deliveries and which
  teammate usually wins the first contact, built from
  :func:`~wa_setpieces.core.phases.classify_phase`'s own
  ``first_contact_*`` fields (scoped to contacts the delivering team
  itself won). The first node-link graph in this module -- every other
  multi-entity chart here compares a fixed small set of teams or
  categories, not an open set of players connected by
  who-delivers-to-whom. Nodes sit evenly around a circle; edge width is
  pairing frequency, node size is total involvement.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_metric_histogram` -- a
  classic binned histogram of any continuous metric, with no smoothing
  assumption baked in the way :func:`plot_value_distribution`'s violins
  and :func:`plot_value_ridgeline`'s KDE curves both have.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_value_boxplot` --
  exact quartiles, median and outliers per set-piece type, for when the
  specific numbers matter more than the overall distribution shape.
- Three new gallery examples (``plot_37``-``plot_39``); module docstring
  updated.
- 5 new tests (350 total). Docs build clean (39/39 gallery scripts,
  zero warnings); every chart rendered and inspected directly, including
  verifying the combination network's circular node layout actually
  traces a true circle (node size and label length made it look
  irregular at a glance, so this was checked against the computed
  positions directly, not just eyeballed).

0.28.0
------

Three more new chart forms -- a stacked area timeline, a progress ring,
and a first-half/second-half slope chart -- none of which existed
anywhere in the module before. Two real bugs caught and fixed during
verification, not just visual polish.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_type_area_timeline` --
  set-piece attempts over match time, binned by type, as a stacked area
  chart -- the *mix* shifting over the match, not individual events
  (:func:`plot_match_timeline`) or a single cumulative value
  (:func:`plot_set_piece_value_flow`). Caught a real bug in
  verification: two of the categorical palette colors are adjacent
  shades of orange, fine everywhere else they're used but with no gap
  between touching stacked bands "throw in" and "goal kick" blended
  into one indistinguishable region -- fixed with a stroke between
  every band, which guarantees a visible seam regardless of which two
  colors happen to land next to each other.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_success_ring` -- a
  single ratio as a circular progress ring, a different visual metaphor
  for the same job :func:`plot_success_waffle` does with filled squares.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_half_comparison_slope`
  -- each set-piece type's value in the first half versus the second,
  as a two-point connected line, colored by direction of change. Caught
  a real correctness issue in verification: a type with an *unchanged*
  value (first half == second half) was colored the same green as an
  improvement, which is a misleading claim -- "flat" isn't "better" --
  fixed with a third neutral color for exact ties.
- Three new gallery examples (``plot_34``-``plot_36``); module docstring
  updated.
- 7 new tests (345 total). Docs build clean (36/36 gallery scripts,
  zero warnings); every chart rendered and inspected directly, and both
  issues above were caught that way.

0.27.0
------

Three more new chart forms -- zone bubbles, a KPI bullet chart, and a
ridgeline -- none of which existed anywhere in the module before.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_zone_bubble` -- zone
  counts as size-encoded bubbles on the pitch, a more intuitive (if less
  precise for close counts) encoding of "how many" than
  :func:`plot_zone_heatmap`'s color ramp. Each bubble carries its own
  count label so the trade-off costs nothing.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_kpi_bullet` -- a
  compact single-ratio bullet chart against qualitative poor/fair/good
  bands and an optional target tick, built for a dashboard strip of
  several stacked together. Caught and fixed a real spacing bug in
  verification: at the tight default figure height, the row label sat
  close enough to the header band that it read as part of the title
  rather than the chart body -- fixed with a taller default figure and
  a tighter y-range.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_value_ridgeline` -- a
  joyplot of per-delivery added value (:func:`scipy.stats.gaussian_kde`,
  already a transitive dependency via mplsoccer), one smooth density
  curve per set-piece type, for a shape a violin's mirrored outline
  shows less clearly. Each type needs >= 3 non-identical values or it's
  silently skipped.
- Three new gallery examples (``plot_31``-``plot_33``); module docstring
  updated.
- 5 new tests (338 total). Docs build clean (33/33 gallery scripts,
  zero warnings); every chart rendered and inspected directly, and the
  bullet-chart spacing bug above was caught that way.

0.26.0
------

Three more new chart forms -- mosaic, parallel coordinates, dumbbell --
none of which existed anywhere in the module before. All three had a
real legend-placement bug caught and fixed during verification, not
just visual polish.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_type_outcome_mosaic` --
  a Marimekko-style mosaic, segment width = volume (attempts), segment
  height = quality (success rate), so both are visible in one chart
  instead of split across :func:`plot_team_comparison`'s bars and
  :func:`plot_volume_quality_scatter`'s points. Caught two real bugs in
  verification: the legend landed directly on top of a data segment
  (fixed by anchoring it above the mosaic body instead of an in-bounds
  corner), and the sample match's two smallest segments (1-2 attempts)
  had their type-name labels run into each other (fixed with a
  minimum-width threshold below which a label rotates 45° and a
  percentage inside the segment is skipped rather than overlapping).
- **Added**: :func:`~wa_setpieces.viz.plots.plot_team_parallel_coordinates`
  -- the same two-team profile comparison as
  :func:`~wa_setpieces.viz.plots.plot_set_piece_radar`, on straight
  parallel axes instead of a circle, so every metric carries equal
  visual weight instead of however much a polar layout happens to
  exaggerate or compress it.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_team_dumbbell` -- two
  teams' values per category as connected dot pairs, for when the *gap*
  between two series is the thing worth seeing directly. Caught a real
  bug: an auto ``loc="best"`` legend placement landed on top of the
  widest-value row; fixed not by anchoring the legend outside the axes
  (tried first -- it fought the header's own top-margin reservation and
  collided with the title on a short figure instead) but by padding the
  y-axis to create dedicated empty space above the topmost category,
  which stays clear regardless of figure height.
- Three new gallery examples (``plot_28``-``plot_30``); module docstring
  updated.
- 6 new tests (333 total). Docs build clean (30/30 gallery scripts,
  zero warnings); every chart rendered and inspected directly, and all
  three legend bugs above were caught that way, not by the code merely
  running without error.

0.25.0
------

A revamp pass across the *older* plotting functions -- not new chart
types this time, but real defects and thin spots in ones that had been
sitting unpolished since before this gallery's newer additions. Found by
rendering every function against the sample match and actually looking
at the output, the same way every previous chart in this changelog was
verified.

- **Fixed**: :func:`~wa_setpieces.viz.plots.plot_second_phase`'s default
  title was silently building "set piece — eventId ... (...)" on *every*
  call, never "corner" or "free kick" -- ``extract_corners``/
  ``extract_free_kicks`` never tagged their rows with ``set_piece_type``,
  so ``classify_phase`` always fell back to the generic label. Also
  fixed: that title routinely overflowed the figure width and rendered
  truncated ("...second-phase sh...") -- shortened to a fixed "Corner
  sequence" / "Free kick sequence" title with the eventId/outcome detail
  moved to the subtitle; and nearby touches in a goalmouth scramble
  stacked into one unreadable blob of overlapping numbers -- fixed with
  a new :func:`~wa_setpieces.viz.plots._declutter_points` helper that
  spreads near-coincident points onto a small rosette. A legend
  (Delivery / Touch / Second-phase shot) was also missing entirely.
- **Fixed**: :func:`~wa_setpieces.viz.plots.plot_defensive_routine_bars`'s
  default title had the same overflow-truncation bug, from the same
  root cause (team-id-in-title on a narrow figure) -- fixed the same
  way, plus added a headline stat strip (``show_stats: bool = True``,
  new parameter) it never had.
- **Fixed**: :func:`~wa_setpieces.viz.plots.plot_xt_added_bars`'s value
  labels used ``bar_label``'s default outside-the-bar placement, which
  collided with the y-axis category label for whichever bar was
  longest (the actual point of a top-N-by-magnitude chart). Replaced
  with labels placed just inside each bar's own tip, which can't
  collide with anything outside the bar.
- **Improved**: :func:`~wa_setpieces.viz.plots.plot_xt_grid` was a bare
  color grid with no way to read an actual value off it -- added
  per-cell value labels (:meth:`mplsoccer.Pitch.label_heatmap`) and a
  colorbar.
- **Improved**: :func:`~wa_setpieces.viz.plots.plot_corner_sonar` had no
  legend distinguishing successful (green) from unsuccessful (red)
  deliveries -- added one, matching the convention already used by
  :func:`~wa_setpieces.viz.plots.plot_delivery_map`.
- Docs build clean (27/27 gallery scripts, zero warnings), 327 tests
  still passing (unchanged -- this pass touched rendering, not the
  underlying data functions).

0.24.0
------

Four more new chart forms -- waterfall, violin, radial bar, waffle --
continuing straight on from 0.23.0's Sankey and beeswarm. None of these
existed anywhere in the module before.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_value_waterfall` -- one
  team's total set-piece added value, decomposed by restart type as a
  floating-bar waterfall stepping to a final total. Caught and fixed a
  real bug during verification: the final "Total" bar always drew
  upward from zero regardless of sign, so a net-negative total (the
  sample team's actual case) rendered as a misleadingly tall bar
  pointing the wrong way -- fixed to span ``[min(0, total), max(0,
  total)]``.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_value_distribution` --
  a violin per set-piece type of per-delivery added value, for the
  *spread* a bar chart's average hides.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_type_radial_bar` -- a
  wind-rose bar chart of one metric across set-piece types. Caught and
  fixed a label-collision bug during verification: value labels placed
  just beyond each bar's tip collided with the category-name ring for
  whichever bar happened to be tallest; fixed by placing labels inside
  each wedge (at least 14% of the max value out from the pole, so short
  wedges don't cluster at the center either) with a dark stroke outline
  so they stay legible over both colored bars and the plain background.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_success_waffle` -- a
  single ratio as a filled-square icon array, for a headline number
  that deserves more visual weight than a stat-strip figure.
- Four new gallery examples (``plot_24``-``plot_27``); module docstring
  updated.
- 8 new tests (327 total, up from 319). Docs build clean (27/27 gallery
  scripts executed, zero warnings); every chart rendered and inspected
  directly, and both bugs above were caught by looking at the actual
  output, not by the code merely running without error.

0.23.0
------

Two genuinely new chart forms, not more variations on bars/scatter/pitch
maps -- requested after the gallery rebuild in 0.22.0 still rendered the
same images as before it (that rebuild only reorganized scripts; the
plotting functions themselves hadn't changed).

- **Added**: :func:`~wa_setpieces.viz.plots.plot_outcome_flow` -- a
  Sankey-style flow diagram from every delivery, through its
  :func:`~wa_setpieces.core.outcomes.delivery_outcomes` category, down to
  whether it ended in a goal. Ribbon width is proportional to delivery
  count at every stage, built from scratch on cubic-Bezier ``PathPatch``
  ribbons (:func:`~wa_setpieces.viz.plots._flow_ribbon`) since matplotlib
  has no built-in proportional Sankey. No chart in this module previously
  showed a *funnel* -- verified against both the zero-goal sample-match
  case (ribbons flow straight through, "Goal" node omitted entirely
  rather than drawn empty) and a synthetic multi-goal case (diagonal
  ribbons correctly split and cross into the "Goal" node).
- **Added**: :func:`~wa_setpieces.viz.plots.plot_rating_beeswarm` -- every
  player as one dot on a 0-100 rating scale, deterministically spread
  just enough to avoid overlap
  (:func:`~wa_setpieces.viz.plots._beeswarm_offsets`, a binned
  alternate-side stack, not a random jitter or a physics packing).
  Answers a different question than :func:`plot_rating_benchmark`'s
  ranked bars: how *spread out* a group's ratings are, not each player's
  rank. Labels push outward in whichever direction their own dot is
  already displaced, so they clear a tightly packed cluster instead of
  colliding with the next dot up.
- Two new gallery examples (``plot_22_outcome_flow.py``,
  ``plot_23_rating_beeswarm.py``); ``categories.rst`` updated to mention
  the flow diagram alongside the corner/free-kick outcome tools.
- 6 new tests (319 total). Docs build clean (23/23 gallery scripts
  executed, zero warnings), every new chart rendered and inspected
  directly, including a synthetic dataset built specifically to exercise
  the goal-split ribbon path the real (goal-less) sample match can't.

0.22.0
------

Rebuilt the whole gallery from scratch: every example script deleted and
rewritten, renumbered 1-21 as a single ordered curriculum (basics, then
non-pitch views, then value/rating/report chains, then the ML and
data-driven extras) instead of the ad-hoc ordering it had accumulated.
No plotting-function changes -- this is a content/structure rebuild only.

- The three newest chart types stay front and center where they were
  already integrated: :func:`~wa_setpieces.viz.plots.plot_zone_scatter`
  leads the zone page, :func:`~wa_setpieces.viz.plots.plot_volume_quality_scatter`
  leads the team-comparison page, and
  :func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow` leads the
  timeline page.
- Every script re-verified end to end: a full Sphinx-Gallery build
  executed all 21 out of 21 files with zero warnings (``-W
  --keep-going``), 313 tests still pass, and several rendered PNGs were
  opened and looked at directly, not just checked for a clean exit code.

0.21.0
------

Three new chart types, not just a redesign of the existing ones -- each
answers a question none of the current plots could, replacing the
corresponding basic chart as the featured example in the gallery.

- **Added**: :func:`~wa_setpieces.viz.plots.plot_zone_scatter` -- every
  event as its own point, colored by outcome, density-shaded by default.
  The individual-event alternative to :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`'s
  binned grid: a grid answers "how many landed in this rectangle," this
  answers "where exactly, and did it work" -- no bin-size choice
  implicitly deciding how coarse the picture is. Now the featured example
  in the gallery's zone page; the grid is still there for exact counts.
- **Added**: :func:`~wa_setpieces.viz.plots.plot_set_piece_value_flow` --
  cumulative set-piece added value per team, over match time, as a step
  chart. A genuinely new analytical angle this package didn't have at
  all: *when* threat was created, not just the final total. Built from
  :func:`~wa_setpieces.core.value.set_piece_added_value` merged back to
  each delivery's ``timeMin`` (scoped to ``(eventId, contestantId)``
  together, since ``eventId`` alone collides across teams).
- **Added**: :func:`~wa_setpieces.viz.plots.plot_volume_quality_scatter`
  -- a labeled quadrant scatter (volume vs. quality, median reference
  lines) for any :func:`~wa_setpieces.set_piece_summary`-shaped table.
  Answers a question no single bar-chart metric can: does the
  type/team with the most attempts also convert them, or is high volume
  masking low quality.
- Three gallery examples updated to feature the new charts as the lead
  visual (``plot_02_delivery_zones.py``, ``plot_06_team_comparison.py``,
  ``plot_09_match_timeline.py``), each verified by rendering and looking
  at the actual output, not just checking it builds.

313 tests passing (unchanged), docs build clean.

0.20.0
------

The gallery looked polished but shallow after 0.19.2's quality pass --
every chart plotted the data and left the reader to work out the
takeaway. This adds the layer that was actually missing: charts that
state their own headline number, and one chart (the delivery map) that
can show the *shape* of a pattern, not just individual deliveries.

- **Added**: an auto-computed headline stat strip -- bold value, muted
  label, e.g. "9 deliveries / 22% success rate" -- under the subtitle on
  :func:`~wa_setpieces.viz.plot_delivery_map`,
  :func:`~wa_setpieces.viz.plot_zone_heatmap` (count and the busiest
  zone's share of it), :func:`~wa_setpieces.viz.plot_corner_sonar`, and
  :func:`~wa_setpieces.viz.plot_dashboard` (attempts/success rate/goals
  for the report's own team). New ``show_stats: bool = True`` parameter
  on each -- on by default; every value is computed straight from the
  data being plotted, never passed in, so it can't drift out of sync
  with the chart. New :meth:`~wa_setpieces.viz.theme.Palette.draw_stat_strip`
  is the shared, reusable building block.
- **Added**: ``density: bool = False`` on
  :func:`~wa_setpieces.viz.plot_delivery_map` -- a kernel-density shade
  of where deliveries land, underneath the arrows
  (:meth:`mplsoccer.Pitch.kdeplot`, via seaborn -- already a transitive
  dependency of mplsoccer, no new dependency added). Off by default: a
  smooth density surface implies a continuous pattern a single match's
  handful of deliveries can't actually support -- meaningful once turned
  on for a season's worth.
- Hero image and all gallery plots regenerated; a new example
  (``plot_21_vertical_pitch.py`` from 0.19.3, already covering
  orientation) sits alongside the existing set -- no new gallery script
  needed for this change, since the enhancement applies to functions
  already demonstrated throughout the gallery.

313 tests passing (unchanged), docs build clean.

0.19.3
------

- **Added**: ``vertical: bool = False`` on every pitch-based plotting
  function -- :func:`~wa_setpieces.viz.plot_delivery_map`,
  :func:`~wa_setpieces.viz.plot_zone_heatmap`,
  :func:`~wa_setpieces.viz.plot_xt_grid`,
  :func:`~wa_setpieces.viz.plot_second_phase`,
  :func:`~wa_setpieces.viz.plot_set_piece_outcomes`,
  :func:`~wa_setpieces.viz.plot_routine_clusters`, and
  :func:`~wa_setpieces.viz.plot_dashboard` (which draws two of them).
  Draws on :class:`mplsoccer.VerticalPitch` (goal-at-top) instead of the
  default :class:`mplsoccer.Pitch` (goal-at-right) -- both classes share
  mplsoccer's own drawing API, so nothing else about a call changes; a
  zone heatmap's grid rotates with the pitch too (6x3 becomes 3x6), not
  just the outline.
- The default vertical canvas (5.6in x 8.2in) is taller/narrower than
  the horizontal default (8in x 5.2in), so a portrait pitch doesn't sit
  in a landscape canvas with wasted space on either side.
- New gallery example, ``plot_21_vertical_pitch.py``, showing the same
  deliveries and zone heatmap in both orientations side by side.
- Noted in :func:`~wa_setpieces.viz.plot_dashboard`'s docstring:
  ``vertical=True`` there letterboxes the two pitch panels within their
  existing landscape-shaped grid cells rather than reshaping the cells
  themselves -- usable, but the standalone functions are the better fit
  for a vertical pitch as the main image.

313 tests passing (unchanged), docs build clean.

0.19.2
------

Visual quality pass on :mod:`wa_setpieces.viz`, prompted by feedback that
the gallery didn't feel "befitting" the package's own WA branding --
found several concrete, real problems by actually rendering and looking
at the output, not just guessing at what "higher quality" might mean.

- **Fixed a real bug**: a long header title collided with the WA lockup
  on narrower figures (e.g. the polar sonar plot, 6in wide) -- confirmed
  by rendering. :meth:`~wa_setpieces.viz.theme.Palette.draw_header` now
  draws the lockup first, measures its actual left edge, and truncates
  the title/subtitle with an ellipsis (measured, not guessed) so they
  stop short of it instead of running through it.
- **Fixed a real bug**: bar-chart y-axis labels (team/player IDs) were
  truncated, missing their first character, on every horizontal bar
  chart -- the default matplotlib left margin didn't account for label
  width. New ``_reserve_ytick_margin`` measures the widest rendered
  label and reserves exactly enough space.
- **Fixed a design flaw**: the sequential heatmap ramp (zone counts, xT
  grids) used a fixed light-to-dark palette designed for a white
  background -- on the dark navy canvas its pale pastel low end looked
  like a different, lighter-themed app pasted into the WA card. Ramps
  are now mode-aware: the low end blends toward *this palette's own
  surface color* (receding into the canvas) and only the high end (WA's
  saturated categorical hue) is fixed across both modes.
- **Added**: value labels (``ax.bar_label``) on every bar chart --
  team comparison, xT-added bars, rating benchmark, defensive routine
  bars, aerial duel win rate -- reading exact values off a bar no longer
  requires eyeballing against gridlines.
- **Changed**: delivery-map arrows are bolder (wider, larger heads) and
  bar-chart gridlines lighter/more subtle, closer to how the reference
  WA report charts actually look rather than matplotlib defaults.
- **Changed**: gallery images render at 200 dpi in the docs build
  (was matplotlib's default 100) -- crisper text and lines once a
  browser displays the image at its natural size.
- Hero image and all twenty gallery plots regenerated, in both light and
  dark mode, and visually reviewed image by image before committing --
  not just checked for a clean build.

313 tests passing (was 310; two sequential-cmap tests rewritten for the
new mode-aware ramp direction, one new test added), docs build clean.

0.19.1
------

Wording-only pass -- no functional or schema change. "F24" (the Opta/
Stats Perform event-feed name) is still this package's native format,
exactly as before -- only the word itself is gone from docs, docstrings,
comments and the changelog, replaced with "Opta" or "the (event) feed"
depending on context. Applied everywhere it appeared: README, every
``docs/source/*.rst`` page, every module docstring and inline comment in
``src/``, the example scripts and notebooks, and past changelog entries.

310 tests passing (unchanged), docs build clean.

0.19.0
------

Every plot in :mod:`wa_setpieces.viz` gets a real chart "card" anatomy
now, not just a colored title -- the same WA house-style card layout
used in Waltzing Analytics' own report work, generalized into the
package's shared theme so every function gets it automatically.

- **Added**: a header band (eyebrow category label, serif title, muted
  subtitle) and the "WA · WALTZING ANALYTICS" brand lockup, top-right of
  every chart that owns its own figure -- on by default, since this is
  the package's own brand mark, not any individual's. New
  :meth:`~wa_setpieces.viz.theme.Palette.draw_header`/:meth:`~wa_setpieces.viz.theme.Palette.draw_wa_lockup`/
  :meth:`~wa_setpieces.viz.theme.Palette.draw_eyebrow`/:meth:`~wa_setpieces.viz.theme.Palette.draw_footer`
  on :class:`~wa_setpieces.viz.theme.Palette`.
- **Added**: ``eyebrow`` and ``author`` parameters on every plotting
  function in :mod:`wa_setpieces.viz.plots`. ``author`` adds a personal
  byline under the WA lockup and a "{author} | Created on DD-MM-YYYY"
  stamp to the footer -- opt-in, no default, so a chart from this
  package never carries a name that isn't yours.
- **Changed**: the footer's ``source``/credit text (the pre-existing
  ``footer=`` argument) moved from bottom-right to bottom-left, to make
  room for the new author/date stamp on the right.
- **Changed**: when a plotting function creates its own figure (i.e.
  ``ax`` wasn't passed in), title/subtitle now render in this new
  figure-level header band instead of as the axes' own
  ``ax.set_title()`` -- ``ax.get_title()`` is empty in that case now.
  Passing your own ``ax`` still uses the older, simpler axes-level title
  (this function doesn't own the whole figure in that case and can't
  safely reserve header margin on it).
- **Fixed**: a real layout bug this surfaced -- :func:`mplsoccer.Pitch.draw`
  turns on a ``TightLayoutEngine`` by default, which silently re-runs on
  every subsequent draw/save and overrides ``subplots_adjust``, undoing
  reserved header/footer margins the moment a pitch-based figure is
  saved (confirmed by rendering: the title drew directly on top of the
  legend). Fixed by disabling the figure's layout engine once the WA
  card's own margins are set.
- Hero image and all twenty gallery plots regenerated against the new
  anatomy, in both light and dark mode.

310 tests passing (was 309; the axes-title behavior change above gets
its own regression test alongside the updated one), docs build clean.

0.18.7
------

Docs-only removal -- no library code changed.

- **Removed**: the narrative ``user_guide/`` pages (nine files), the
  Opta qualifier reference (``qualifiers.rst``) and the API reference
  (``api.rst``, and with it ``sphinx.ext.autodoc``/``napoleon``/``viewcode``
  from the Sphinx build -- nothing left to generate). The six "pick one,
  see how it works" reference pages (:doc:`categories`, :doc:`value_models`,
  ``by_metric``, ``by_phase``, ``by_routine``, ``by_report``) are now the
  whole of the docs past install/quickstart/gallery -- every cross-reference
  that pointed into a removed page was retargeted at its replacement, or
  dropped where no direct replacement exists.
- ``:func:``/``:class:``/``:mod:`` roles throughout the docs (there are
  many) still parse fine without ``autodoc`` loaded -- they're core Sphinx
  Python-domain roles -- they just render as plain code text now instead
  of a hyperlink, since there's no API reference page left to link to.

309 tests passing (unchanged -- docs only), docs build clean, zero
Sphinx warnings.

0.18.6
------

Docs-only addition, completing the reference-page pattern 0.18.5 started
for value models -- no library code changed.

- **Four new pages**: ``by_metric.rst``, ``by_phase.rst``,
  ``by_routine.rst``, ``by_report.rst`` -- the same pick-one-see-how-it-works
  reference :doc:`categories`/:doc:`value_models` give set pieces and value
  models, now for the remaining four ``user_guide`` topics (metrics/
  deliveries/zones, second phases/retention/outcomes, routines/long
  throws/penalties, reports/export/CLI). Every entry follows the same
  What it returns/detects/describes/produces, Requirements, Compute it,
  Where it's used template, cross-linked back to its narrative guide page
  and forward to whatever consumes it.
- Every code snippet in all four pages -- including every CLI subcommand
  in ``by_report.rst`` -- was executed against the bundled sample match
  to confirm it actually runs.
- Homepage and quickstart "where next" sections now list all six
  reference pages together.

309 tests passing (unchanged -- docs only), docs build clean.

0.18.5
------

Docs-only addition, following up on 0.18.4's restructure -- no library
code changed.

- **New page**: ``value_models.rst`` ("By value model") -- the same
  pick-one-see-what-it-does reference :doc:`categories` gives set pieces,
  but for the value-model layer: xT, added value, the experimental
  ML-based shot value, and team/player/defensive rating -- what each one
  measures, what it needs, and a runnable example, plus a short diagram
  of how they chain together (xT -> added value -> ratings).
- **``categories.rst``**: every set-piece section now has runnable code
  boxes alongside the prose (export/metrics/value model/visualisation),
  matching every other page in the docs -- previously prose-and-cross-refs
  only.
- Every code snippet in both pages was executed against the bundled
  sample match to confirm it actually runs, including the ``ml`` extra's
  shot-value path.

309 tests passing (unchanged -- docs only), docs build clean.

0.18.4
------

Docs rewrite and a house-style pass -- no library code changed, only
documentation content/build and the chart palette.

- **Docs restructure**: the old two-page ``quickstart``/``advanced`` wall
  split into a proper mplsoccer-style user guide -- eight focused,
  example-first pages under ``user_guide/`` (loading, metrics,
  phases/outcomes, value/ratings, routines, defending/season, reports/
  export, visualisation), plus a new ``categories.rst`` "By set piece"
  reference organized by set-piece type (corner, free kick, throw-in,
  penalty, goal kick, kick-off) rather than pipeline stage. ``api.rst``
  regrouped into the same six sections instead of one flat module list.
- **Docs theme**: switched from ``pydata-sphinx-theme`` (top navbar) to
  ``sphinx-rtd-theme`` -- confirmed against mplsoccer's own built docs
  that this is the theme they actually use, and it's the one with the
  classic always-visible left navigation tree, rather than pydata's
  contextual per-section sidebar.
- **House style**: :mod:`wa_setpieces.viz.theme`'s dark and light chart
  palettes are now Waltzing Analytics' own brand colors (dark navy/coral,
  light paper/amber) instead of a generic blue/orange palette -- four of
  each mode's eight categorical colors, the hairline, ink, muted tones,
  and the team-identity pairing (now teal-then-blue, was orange-then-blue)
  are WA's own documented values; the rest extend from WA's other brand
  hues (confidence green/red, brand amber) to fill out eight categorical
  slots. The docs site chrome (sidebar, links, admonitions) picked up the
  same navy/coral treatment via ``custom.css``. Hero image and all twenty
  gallery plots regenerated against the new palette.

309 tests passing (was 307), docs build clean, zero Sphinx warnings.

0.18.3
------

Verification pass on the two lowest-level trust boundaries left with real
gaps: ``core/phases.py`` (the heuristic every set-piece module downstream
ultimately builds on) and ``core/schema.py`` (``validate_events``, the
gatekeeper every adapter's output passes through). No bugs found -- both
already behaved correctly -- but neither had a single test proving it,
which is its own risk on code this central.

- **Tests**: ``_phase_window``'s period-boundary stop (a corner right at
  the end of a half no longer bleeding its follow-up window into the next
  half's kickoff, the intra-match analog of the already-tested
  cross-match boundary) had zero coverage; confirmed correct and locked
  in as a regression test. Same for ``classify_phase``'s two-team guard.
- **Tests**: ``validate_events``'s four other rejection paths (non-``DataFrame``
  input, a non-numeric core column, an implausible coordinate, a missing
  ``contestantId``) were entirely untested beyond the one "missing
  column" case -- all four now have explicit regression tests confirming
  the right error and message.

307 tests passing (was 301), docs build clean.

0.18.2
------

A hygiene pass following up on the pattern behind three prior real bugs
(``QUALIFIER_INSWINGER``, ``QUALIFIER_HEADED``, the goal-mouth-z/xG
collision): a systematic cross-check of every qualifierId constant in the
package against real co-occurrence data in the sample match, plus closing
the one meaningful test-coverage gap it turned up along the way. No live
bugs this time -- everything actually read or written by this package
checked out -- but two constants were simply wrong and sitting unused,
which is exactly how the three prior bugs started.

- **Removed**: ``QUALIFIER_NOT_ASSISTED`` (was 26) and ``QUALIFIER_ASSISTED``
  (was 28) -- both wrong and both unreferenced anywhere in the codebase.
  26 is actually Opta's "Free kick" shot-situation flag (it partitions
  cleanly with four sibling situation qualifiers across every shot in the
  sample, and all three q_26 shots fire directly off a foul with no
  intervening pass); 28 never appears in the sample at all, while 29 --
  the value ``QUALIFIER_ASSIST`` already correctly uses -- does. Neither
  removal fixes a live bug (nothing referenced them), only a landmine for
  whoever reached for them next.
- **Docs**: ``core.placement``'s module docstring now documents the
  qualifier 102/103 confirmation in full (previously only ``goal_y_norm``
  was called confirmed) and a newly-noticed Opta convention: blocked
  shots carry a fixed placeholder ``q_103`` of ``"19"`` (exactly half the
  assumed 0-38 scale) rather than a real height, so ``goal_h_norm`` for a
  blocked shot is a fabricated 0.5, not a measurement.
- **Tests**: closed the one real coverage gap the audit surfaced --
  ``set_piece_added_value``'s branch that actually extracts a
  assist-chain-linked shot's coordinates and computes ``shot_value``/
  ``is_goal`` had never been exercised by any test, because the sample
  match has no *direct* linked shot off a corner or free kick (its two
  corner shots are both second-phase, which the assist-chain qualifier
  doesn't reach). Also closed ``providers/statsbomb.py``'s remaining
  coverage gaps (outswinger technique, headed pass, blocked shot, penalty
  shot) -- both files now at 100%/97%.

0.18.1
------

Bugfix release: a dedicated review of ``convert/corners.py`` (74% test
coverage, the weakest in the package, and never through this project's
earlier section-by-section correctness pass) found five real bugs, all
with regression tests. One of them led to a sixth in
``providers/statsbomb.py``.

- **Fixed**: ``Q_HEADED`` was reading qualifier 22 ("Regular play", a shot
  *situation* flag) instead of 15 ("Head") -- same family as the
  historical ``Q_INSWING = 72`` mistake. Every headed shot/corner was
  mislabelled, and ``_body_part`` additionally always fell back to
  "Right Foot" for left-footed shots since it never checked the left-foot
  qualifier. Centralized as ``constants.QUALIFIER_HEADED`` (15) so
  ``convert.corners`` and ``providers.statsbomb`` share one definition
  instead of each risking their own drift.
- **Fixed**: ``Q_XG`` was reading qualifier 103, which is
  ``core.placement.QUALIFIER_GOAL_MOUTH_Z`` -- the feed has no xG qualifier at
  all, so this was reading goal-mouth-z as if it were an expected-goals
  value (an off-target miss's z of 65.3 became an "xG" of 0.653).
  ``shot.statsbomb_xg`` in ``convert.corners``'s output is now always
  empty, documented in the module docstring.
- **Fixed**: the same qualifier-103 mistake existed on the write side in
  ``providers.statsbomb``, encoding ``statsbomb_xg`` into ``q_103`` --
  colliding with real goal-mouth-z placement and corrupting
  ``ml.shot_value``'s ``goal_h_norm`` feature for every StatsBomb-sourced
  shot with a nonzero xG. StatsBomb's xG has no Opta qualifier to map onto
  and is no longer written.
- **Fixed**: ``_to_sb_y`` rescaled Opta's y coordinate to StatsBomb's
  0-80 scale but never flipped it -- Opta's y origin is the bottom
  touchline, StatsBomb's is the top, so every delivery landed in the
  mirror-image corner of the pitch.
- **Fixed**: ``build_possessions`` incremented on every team alternation,
  but Opta interleaves lone defensive touches into the attacking team's
  own stream, inflating possession counts roughly 3-4x (the sample match:
  ~700 possessions for 1613 events, StatsBomb-plausible is ~200). Combined
  with the shot-linking window's off-by-one tolerance, this meant *zero*
  corner-to-shot links resolved in the sample match even where a real one
  existed a few events later. Now requires two consecutive touches by the
  new team before counting it as a possession change.
- **Fixed**: a blank cell in the match-list CSV parsed to the string
  ``"nan"`` (truthy), defeating the "skip incomplete row" guard and
  keeping id-less rows as matches with a literal ``"nan"`` team name.

``convert/corners.py`` coverage: 74% -> 89%. Full suite: 296 passed,
2 skipped (was 268).

0.18.0
------

A completeness pass prompted by a coverage audit (``cli.py`` 72%,
``convert/corners.py`` 74%, ``core/season.py`` 82%, against ~95%+ for the
rest of the package): closed the gaps that were actually missing
capability rather than just missing tests, and found one more real bug
along the way.

- **New**: ``SeasonDataset.season_report`` -- the whole-season roll-up
  that was missing next to ``.summary()`` (basic counts only) and
  ``.report()`` (the full field set, but one row per team *per match*).
  Sums every count across matches first and re-derives rates from the
  sums, never averaging a per-match rate directly -- the same idiom
  ``rolling_summary``/``rolling_defensive_summary`` already used for a
  trailing window, now applied to the whole season.
- **New CLI**: ``season`` subcommand puts ``SeasonDataset`` on the command
  line (``--action summary|report|season-report|rolling|rolling-defense``);
  ``scout`` puts ``opponent_scouting_report_html`` on the command line.
  Both were Python-only before.
- **Improved CLI**: ``report --type corner`` now writes the curated
  ``corner_report_html`` (rating, outcome/routine breakdowns, delivery/
  outcome maps) instead of a generic table dump; other types still use
  the generic dump since there's no curated report for them yet.
  ``workflow`` gained ``--format csv|xlsx`` (was CSV-only).
- **Fixed a real bug**: ``load_events_multi`` (and therefore
  ``SeasonDataset.from_sources`` and the new ``season``/``scout``/
  ``train-xt`` CLI commands) derived a default ``matchId`` from each
  source's filename stem with no collision check -- two sources sharing a
  stem (the same filename from two different directories, or the same
  file passed twice by mistake) silently merged under one ``matchId``,
  defeating every match-safety guarantee built on top of it being unique.
  Found while manually testing the new ``season`` CLI subcommand with a
  copy-pasted example. Now raises a clear ``ValueError`` naming the
  colliding sources, for both default and explicitly-passed ``match_ids``.
- **Docs**: deduplicated two README sections that had drifted into
  covering the same ``SeasonDataset`` ground (one had gained the CLI
  section wedged in between them); ``core.attribution`` and
  ``XTModel.save``/``.load`` persistence, previously only mentioned in
  passing, now have real usage examples.

0.17.1
------

Bugfix release: the cross-match ``eventId``-collision defect fixed in
0.13.x/0.14.x for ``chains``/``metrics``/``value``/``shot_value`` turned out
to have three more instances in modules built after that fix, found by a
targeted audit of every module touching a raw ``eventId`` lookup. All three
only misfire on a multi-match frame (``SeasonDataset``/``load_events_multi``)
that shares ``eventId`` values across matches for the same team -- a normal
single match is unaffected -- and all three are covered by new regression
tests that fail against the pre-fix code.

- **Fix**: ``delivery_outcomes`` (and therefore ``outcome_summary``,
  ``aerial_duel_summary``) resolved a delivery's first-contact/aerial event
  by bare ``(contestantId, eventId)``, with no per-match loop. On a
  multi-match frame this silently returned whichever match's row came
  first in the concatenated frame for *every* delivery -- most visibly,
  misattributing who won an aerial duel. Now match-safe the same way
  ``restart_routines`` already was, and carries a ``matchId`` column when
  the input has one.
- **Fix**: ``core.attribution.first_contact_detail`` looked ahead by row
  position with only a ``periodId`` check, so a delivery near the end of
  one match could pick up an unrelated event from the start of the next
  match (clock reset to ~0) as its "first contact". Now loops per match
  like ``restart_routines``/``delivery_outcomes`` and carries ``matchId``.
- **Fix**: ``core.routines.long_throw_second_phases`` built ``matchId``-aware
  keys to pick out long throws but then handed ``classify_phase`` the
  *whole* multi-match frame, which walks forward by position and only
  breaks on a ``periodId`` change -- the same failure mode as the
  ``first_contact_detail`` bug above, for the one throw-in path that reuses
  ``classify_phase`` directly. Now classifies each throw-in against its own
  match's events only.
- **Improved**: ``penalty_placement_detail`` now carries a ``matchId``
  column when the input has one (previously the only per-restart detail
  table that didn't), so a penalty's ``eventId`` stays attributable to the
  right match on a season-combined frame.

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
  ``wa_setpieces.core.loader.load_events`` produces from Opta, so
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
  pyarrow) batch-converts a directory of Opta match JSON exports, plus
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
  models' training feature schema from Opta qualifiers, reusing
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

- **Fixed a real correctness bug**: the feed's ``eventId`` is only unique
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
- ``wa_setpieces.load_events_multi``: loads and stacks several Opta exports
  into one events DataFrame tagged with a ``matchId`` column, for
  match-independent aggregation (team/player counts, zone heatmaps,
  fitting ``XTModel`` across a season) -- documented as unsafe to feed
  directly into the per-match ``phases``/``retention`` window functions.
- Fixed ``plot_match_timeline``'s minute axis: Opta's ``timeMin`` already
  runs cumulatively across periods in this feed (period 2 continues from ~45,
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
  free kicks, corners, throw-ins and goal kicks from Opta event data.
- Set-piece-to-shot/goal chain linking via the assist-chain qualifier.
- ``wa-setpieces`` command-line tool.
