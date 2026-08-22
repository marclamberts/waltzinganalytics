.. _by-category:

By set piece
============

Everything else on this site is organized by *pipeline stage* (loading,
extracting, metrics, value, viz...). This page is organized the other
way around: pick your set piece, then pick what you want from it --
**export**, **metrics**, **value model** or **visualisation**. Each entry
links to the full writeup elsewhere in the docs. Looking for a value
model instead of a set piece? :doc:`value_models` is the same idea,
organized the other way around.

All six types share one entry point --
:func:`~wa_setpieces.run_workflow` -- so nothing below requires learning
a different API per type; the difference between categories is which
fields of the returned :class:`~wa_setpieces.core.workflow.SetPieceWorkflow`
come back populated instead of ``None``. See :ref:`coverage-matrix` at
the bottom for the field-by-field breakdown.

.. code-block:: python

   from wa_setpieces import run_workflow, XTModel

   model = XTModel.fit(match.events)  # only unlocks value/rating for corner + free kick
   result = run_workflow(match.events, "corner", model=model)  # swap "corner" for any type below

.. code-block:: bash

   wa-setpieces workflow match.json --type corner --output tables/ --format xlsx

Corner
------

The most complete pipeline in the package -- the reference case every
other type is measured against below.

**Export to CSV/Excel**
   :func:`~wa_setpieces.save_table`/:func:`~wa_setpieces.save_tables` take
   any single table or the whole
   :class:`~wa_setpieces.core.workflow.SetPieceWorkflow`. See
   :doc:`user_guide/reports_and_export`.

   .. code-block:: bash

      wa-setpieces workflow match.json --type corner --format xlsx --output tables/

**Metrics to pull**
   :func:`~wa_setpieces.set_piece_summary`/:func:`~wa_setpieces.team_set_piece_counts`/
   :func:`~wa_setpieces.player_set_piece_counts` (attempts, success rate),
   :func:`~wa_setpieces.delivery_locations` (start/end coordinates),
   :func:`~wa_setpieces.core.phases.second_phases` (cleared / first-phase
   shot / second-phase shot), :func:`~wa_setpieces.core.retention.retention_detail`
   (still in possession ~8s later), :func:`~wa_setpieces.core.attribution.first_contact_detail`
   and :func:`~wa_setpieces.core.outcomes.aerial_duel_summary` (who wins
   the first header), plus the full :doc:`routine taxonomy
   <user_guide/routines>` (inswinger/outswinger, near/far/central target,
   rule-based *and* k-means routine clusters).

   .. code-block:: python

      from wa_setpieces import delivery_locations, second_phases, retention_rate

      corners = delivery_locations(match.events, "corner")
      second_phases(match.events, "corner")
      retention_rate(match.events, "corner")

**Value model**
   Fully supported -- corner is one of the two phase-based types (with
   free kick) that :func:`~wa_setpieces.core.value.set_piece_added_value`
   and player :func:`~wa_setpieces.core.rating.player_rating` cover.
   Needs a fitted :class:`~wa_setpieces.XTModel` (``XTModel.fit(events)``
   over a season, not one match). Produces per-delivery xT added, the
   quality of any resulting shot, a 0-100 team rating and a split
   delivery/finishing player rating. See :doc:`value_models`.

   .. code-block:: python

      from wa_setpieces import set_piece_added_value, team_rating, player_rating, corner_report

      set_piece_added_value(match.events, "corner", model)          # per-delivery
      team_rating(corner_report(season_events, model=model))        # 0-100 per team
      player_rating(season_events, "corner", model)                 # delivery/finishing split

**Visualisation**
   The full plot set applies, plus two corner-only plots:
   :func:`~wa_setpieces.viz.plots.plot_corner_sonar` (delivery angle +
   distance, polar) and the curated
   :func:`~wa_setpieces.corner_report_html` self-contained HTML report
   -- the only type with a bespoke report; every other type falls back to
   a generic table dump. See the :ref:`gallery`.

   .. code-block:: python

      from wa_setpieces.viz.plots import plot_delivery_map, plot_corner_sonar

      plot_delivery_map(corners, title="Corner deliveries")
      plot_corner_sonar(corners, title="Corner sonar")

   .. code-block:: bash

      wa-setpieces report match.json --type corner --model league-model.npz --output report.html

Free kick
---------

The other phase-based type -- everything corner gets *except* the
curated HTML report and the sonar plot.

**Export to CSV/Excel**
   Same mechanism as corner, above.

   .. code-block:: bash

      wa-setpieces workflow match.json --type free_kick --format xlsx --output tables/

**Metrics to pull**
   Same set as corner: summary/counts, delivery locations, second
   phases, retention, first contacts, aerial duels, full routine
   taxonomy and clusters. Free-kick-specific origin zone (direct/wide/deep)
   comes from the same routine feature extraction as corner's
   near/far/central target -- see :doc:`user_guide/routines`.

   .. code-block:: python

      from wa_setpieces import delivery_locations, second_phases, restart_routines

      free_kicks = delivery_locations(match.events, "free_kick")
      second_phases(match.events, "free_kick")
      restart_routines(match.events, "free_kick")

**Value model**
   Fully supported, identical mechanism to corner -- added value, team
   rating and player rating all work from the same
   :class:`~wa_setpieces.XTModel`. See :doc:`value_models`.

   .. code-block:: python

      from wa_setpieces import set_piece_added_value, free_kick_report, team_rating

      set_piece_added_value(match.events, "free_kick", model)
      team_rating(free_kick_report(season_events, model=model))

**Visualisation**
   The general plot set (delivery map, zone heatmap, second-phase
   sequence, xT added bars, radar, dashboard, timeline) -- everything
   corner has except :func:`~wa_setpieces.viz.plots.plot_corner_sonar`
   and the curated HTML report. ``wa-setpieces report match.json --type
   free_kick --output report.html`` still works, but produces the
   generic table dump, not a bespoke layout.

   .. code-block:: python

      from wa_setpieces.viz.plots import plot_delivery_map, plot_xt_added_bars

      plot_delivery_map(free_kicks, title="Free-kick deliveries")

Throw-in
--------

No xT value model (throw-ins are a possession restart, not a shot-threat
delivery), but the one type with its own specialist-detection layer on
top of the shared pipeline.

**Export to CSV/Excel**
   Includes ``long_throw_taker_summary``/``long_throw_second_phases``
   alongside the shared tables.

   .. code-block:: bash

      wa-setpieces workflow match.json --type throw_in --format xlsx --output tables/

**Metrics to pull**
   Summary/counts, delivery locations, retention, first contacts, full
   routine taxonomy/clusters -- plus two throw-in-only tables:
   :func:`~wa_setpieces.core.routines.long_throw_taker_summary` (per-player
   long-throw volume and threat created) and
   :func:`~wa_setpieces.core.routines.long_throw_second_phases` (flick-on/knockdown
   detection restricted to throws past a distance threshold, default
   25m). See :doc:`user_guide/routines`. No second-phase
   detection or aerial-duel summary on the general (non-long) throw-in
   set -- those are corner/free-kick-only.

   .. code-block:: python

      from wa_setpieces import long_throw_taker_summary, long_throw_second_phases

      long_throw_taker_summary(match.events, min_distance=25.0)
      long_throw_second_phases(match.events, min_distance=25.0)

**Value model**
   Not available -- ``added_value``/``player_rating`` are ``None`` for
   this type (no :class:`~wa_setpieces.XTModel` link; a throw-in's value
   is better read off ``long_throw_taker_summary``'s threat-created
   column and the routine target matrix than a single xT number). Team
   rating still works, built from success rate and retention rate
   instead. See :doc:`value_models`.

   .. code-block:: python

      from wa_setpieces import team_rating, set_piece_report

      team_rating(set_piece_report(season_events, "throw_in"))  # no model= -- none applies

**Visualisation**
   :func:`~wa_setpieces.viz.plots.plot_delivery_map` and
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap` work unchanged
   (throw-ins are pass-based, same coordinate schema as corners).
   :func:`~wa_setpieces.viz.plots.plot_routine_clusters` and
   :func:`~wa_setpieces.viz.plots.plot_team_comparison` also apply. No
   xT-bars/radar/sonar (those need the value model above).

   .. code-block:: python

      from wa_setpieces import delivery_locations
      from wa_setpieces.viz.plots import plot_delivery_map

      throw_ins = delivery_locations(match.events, "throw_in")
      plot_delivery_map(throw_ins, title="Throw-ins")

Penalty
-------

Structurally different from the other five -- detected on the shot
event itself, not a pass, so most of the shared delivery/phase machinery
doesn't apply and isn't run.

**Export to CSV/Excel**
   A much shorter table set than the pass-based types (see below).

   .. code-block:: bash

      wa-setpieces workflow match.json --type penalty --format xlsx --output tables/

**Metrics to pull**
   Summary/counts, plus two penalty-only tables:
   :func:`~wa_setpieces.core.penalties.penalty_placement_detail` (goal-mouth
   zone: which of the six placement zones each penalty targeted) and
   :func:`~wa_setpieces.core.penalties.penalty_taker_summary` (per-player
   conversion rate). See :doc:`user_guide/routines`.
   ``deliveries``, ``second_phases``, ``retention`` and ``first_contacts``
   are all ``None`` -- there's no pass to extract coordinates from and no
   restart-to-retention window to measure.

   .. code-block:: python

      from wa_setpieces import penalty_placement_detail, penalty_taker_summary

      penalty_placement_detail(match.events)
      penalty_taker_summary(match.events)

**Value model**
   Not the xT model -- a penalty's value is its conversion rate and
   placement, not delivery threat. No ``added_value``/``player_rating``.
   Team rating still runs, from success rate alone. See :doc:`value_models`.

   .. code-block:: python

      from wa_setpieces import team_rating, set_piece_report

      team_rating(set_piece_report(season_events, "penalty"))

**Visualisation**
   No delivery map (no delivery). Placement is best read straight off
   :func:`~wa_setpieces.core.penalties.penalty_placement_detail`'s zone
   column (a goal-mouth grid) rather than a dedicated plot function --
   there isn't one yet.

   .. code-block:: python

      placement = penalty_placement_detail(match.events)
      placement[["playerName", "result", "corner_zone", "placement_score"]]

Goal kick
---------

Runs the full shared pipeline (this *is* a pass-based restart with
start/end coordinates), just without the phase-based value model or any
type-specific extras of its own.

**Export to CSV/Excel**

   .. code-block:: bash

      wa-setpieces workflow match.json --type goal_kick --format xlsx --output tables/

**Metrics to pull**
   Summary/counts, delivery locations, retention, first contacts, full
   routine taxonomy/clusters, defensive conceding summary. No
   second-phase detection or aerial-duel summary (corner/free-kick-only),
   and no goal-kick-specific extras the way throw-in has long throws or
   penalty has placement.

   .. code-block:: python

      from wa_setpieces import delivery_locations, retention_rate, defensive_set_piece_summary

      goal_kicks = delivery_locations(match.events, "goal_kick")
      retention_rate(match.events, "goal_kick")
      defensive_set_piece_summary(match.events)

**Value model**
   Not available -- same reasoning as throw-in: no
   :class:`~wa_setpieces.XTModel` link for this type yet, so
   ``added_value``/``player_rating`` are ``None``. Team rating runs from
   success rate and retention rate. See :doc:`value_models`.

   .. code-block:: python

      from wa_setpieces import team_rating, set_piece_report

      team_rating(set_piece_report(season_events, "goal_kick"))

**Visualisation**
   General plot set: :func:`~wa_setpieces.viz.plots.plot_delivery_map`,
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`,
   :func:`~wa_setpieces.viz.plots.plot_routine_clusters`,
   :func:`~wa_setpieces.viz.plots.plot_team_comparison`. No xT-based
   plots (needs the value model above).

   .. code-block:: python

      from wa_setpieces.viz.plots import plot_zone_heatmap
      from wa_setpieces.core.zones import add_channels

      plot_zone_heatmap(add_channels(goal_kicks, y_col="end_y", n=5), title="Goal-kick landing channels")

.. _kick-off-coming-soon:

Kick off (coming soon)
-----------------------

Detected and extracted today -- the basics work now -- but without any
of the type-specific depth the other five have, so treat it as the
least mature category rather than "not implemented."

**What works today**
   Extraction, summary/counts, delivery locations, retention, generic
   routine taxonomy/clusters, and CSV/Excel export -- all through the
   same calls as every other type. General plots
   (:func:`~wa_setpieces.viz.plots.plot_delivery_map`,
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`) render fine on it.

   .. code-block:: python

      from wa_setpieces import extract_kick_offs, delivery_locations, run_workflow

      extract_kick_offs(match.events)
      delivery_locations(match.events, "kick_off")
      run_workflow(match.events, "kick_off")  # no model= -- there's no xT path for this type yet

   .. code-block:: bash

      wa-setpieces workflow match.json --type kick_off --format xlsx --output tables/

**Not yet available**
   No value model (not in the phase-based pair, same as throw-in/goal
   kick), no second-phase or aerial-duel detection, no curated report,
   and no kick-off-specific enrichment (nothing like long-throw
   detection or penalty placement -- there isn't an obvious equivalent
   yet). If you need kick-off analysis today, the generic
   ``run_workflow``/``wa-setpieces workflow --type kick_off`` output is
   real and usable; there just isn't a bespoke layer on top of it yet.

.. _coverage-matrix:

Coverage matrix
----------------

What :func:`~wa_setpieces.run_workflow` actually returns for each type --
a populated field means that piece of analysis runs; ``--`` means the
field comes back ``None`` (either it doesn't apply to that restart type,
or needs the optional ``model``/``ml`` extra).

.. list-table::
   :header-rows: 1
   :widths: 22 10 10 10 10 10 10

   * - Field
     - Corner
     - Free kick
     - Throw-in
     - Penalty
     - Goal kick
     - Kick off
   * - summary / counts
     - yes
     - yes
     - yes
     - yes
     - yes
     - yes
   * - deliveries
     - yes
     - yes
     - yes
     - --
     - yes
     - yes
   * - second_phases
     - yes
     - yes
     - --
     - --
     - --
     - --
   * - retention
     - yes
     - yes
     - yes
     - --
     - yes
     - yes
   * - added_value / player_rating
     - needs model
     - needs model
     - --
     - --
     - --
     - --
   * - first_contacts
     - yes
     - yes
     - yes
     - --
     - yes
     - yes
   * - aerial_duel summaries
     - yes
     - yes
     - --
     - --
     - --
     - --
   * - routines / routine_clusters
     - yes
     - yes
     - yes
     - yes
     - yes
     - yes
   * - type-specific extras
     - --
     - --
     - long throws
     - placement
     - --
     - --
   * - curated HTML report
     - yes
     - --
     - --
     - --
     - --
     - --
   * - team_rating
     - yes
     - yes
     - yes
     - yes
     - yes
     - yes

Every type gets ``team_rating`` regardless of what feeds it -- corner/free
kick blend in added value, the rest score off success rate and retention
rate alone (see :doc:`value_models`).
