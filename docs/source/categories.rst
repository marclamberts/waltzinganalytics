.. _by-category:

By set piece
============

Everything else on this site is organized by *pipeline stage* (loading,
extracting, metrics, value, viz...). This page is organized the other
way around: pick your set piece, then pick what you want from it --
**export**, **metrics**, **value model** or **visualisation**. Each entry
links to the full writeup elsewhere in the docs.

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
   ``wa-setpieces workflow match.json --type corner --format xlsx --output tables/``
   writes every table below as one file. From Python,
   :func:`~wa_setpieces.save_table`/:func:`~wa_setpieces.save_tables` take
   any single table or the whole
   :class:`~wa_setpieces.core.workflow.SetPieceWorkflow`. See
   :doc:`user_guide/reports_and_export`.

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

**Value model**
   Fully supported -- corner is one of the two phase-based types (with
   free kick) that :func:`~wa_setpieces.core.value.set_piece_added_value`
   and player :func:`~wa_setpieces.core.rating.player_rating` cover.
   Needs a fitted :class:`~wa_setpieces.XTModel` (``XTModel.fit(events)``
   over a season, not one match). Produces per-delivery xT added, the
   quality of any resulting shot, a 0-100 team rating and a split
   delivery/finishing player rating. See :doc:`user_guide/value_and_ratings`.

**Visualisation**
   The full plot set applies, plus two corner-only plots:
   :func:`~wa_setpieces.viz.plots.plot_corner_sonar` (delivery angle +
   distance, polar) and the curated
   :func:`~wa_setpieces.corner_report_html` self-contained HTML report
   (``wa-setpieces report match.json --type corner --output report.html``)
   -- the only type with a bespoke report; every other type falls back to
   a generic table dump. Otherwise:
   :func:`~wa_setpieces.viz.plots.plot_delivery_map`,
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`,
   :func:`~wa_setpieces.viz.plots.plot_second_phase`,
   :func:`~wa_setpieces.viz.plots.plot_xt_added_bars`,
   :func:`~wa_setpieces.viz.plots.plot_set_piece_radar`,
   :func:`~wa_setpieces.viz.plots.plot_dashboard` and more -- see the
   :ref:`gallery`.

Free kick
---------

The other phase-based type -- everything corner gets *except* the
curated HTML report and the sonar plot.

**Export to CSV/Excel**
   ``wa-setpieces workflow match.json --type free_kick --format xlsx --output tables/``.
   Same mechanism as corner, above.

**Metrics to pull**
   Same set as corner: summary/counts, delivery locations, second
   phases, retention, first contacts, aerial duels, full routine
   taxonomy and clusters. Free-kick-specific origin zone (direct/wide/deep)
   comes from the same routine feature extraction as corner's
   near/far/central target -- see :doc:`user_guide/routines`.

**Value model**
   Fully supported, identical mechanism to corner -- added value, team
   rating and player rating all work from the same
   :class:`~wa_setpieces.XTModel`. See :doc:`user_guide/value_and_ratings`.

**Visualisation**
   The general plot set (delivery map, zone heatmap, second-phase
   sequence, xT added bars, radar, dashboard, timeline) -- everything
   corner has except :func:`~wa_setpieces.viz.plots.plot_corner_sonar`
   and the curated HTML report. ``wa-setpieces report match.json --type
   free_kick --output report.html`` still works, but produces the
   generic table dump, not a bespoke layout.

Throw-in
--------

No xT value model (throw-ins are a possession restart, not a shot-threat
delivery), but the one type with its own specialist-detection layer on
top of the shared pipeline.

**Export to CSV/Excel**
   ``wa-setpieces workflow match.json --type throw_in --format xlsx --output tables/`` --
   includes ``long_throw_taker_summary``/``long_throw_second_phases``
   alongside the shared tables.

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

**Value model**
   Not available -- ``added_value``/``player_rating`` are ``None`` for
   this type (no :class:`~wa_setpieces.XTModel` link; a throw-in's value
   is better read off ``long_throw_taker_summary``'s threat-created
   column and the routine target matrix than a single xT number). Team
   rating still works, built from success rate and retention rate
   instead.

**Visualisation**
   :func:`~wa_setpieces.viz.plots.plot_delivery_map` and
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap` work unchanged
   (throw-ins are pass-based, same coordinate schema as corners).
   :func:`~wa_setpieces.viz.plots.plot_routine_clusters` and
   :func:`~wa_setpieces.viz.plots.plot_team_comparison` also apply. No
   xT-bars/radar/sonar (those need the value model above).

Penalty
-------

Structurally different from the other five -- detected on the shot
event itself, not a pass, so most of the shared delivery/phase machinery
doesn't apply and isn't run.

**Export to CSV/Excel**
   ``wa-setpieces workflow match.json --type penalty --format xlsx --output tables/`` --
   a much shorter table set than the pass-based types (see below).

**Metrics to pull**
   Summary/counts, plus two penalty-only tables:
   :func:`~wa_setpieces.core.penalties.penalty_placement_detail` (goal-mouth
   zone: which of the six placement zones each penalty targeted) and
   :func:`~wa_setpieces.core.penalties.penalty_taker_summary` (per-player
   conversion rate). See :doc:`user_guide/routines`.
   ``deliveries``, ``second_phases``, ``retention`` and ``first_contacts``
   are all ``None`` -- there's no pass to extract coordinates from and no
   restart-to-retention window to measure.

**Value model**
   Not the xT model -- a penalty's value is its conversion rate and
   placement, not delivery threat. No ``added_value``/``player_rating``.
   Team rating still runs, from success rate alone.

**Visualisation**
   No delivery map (no delivery). Placement is best read straight off
   :func:`~wa_setpieces.core.penalties.penalty_placement_detail`'s zone
   column (a goal-mouth grid) rather than a dedicated plot function --
   there isn't one yet.

Goal kick
---------

Runs the full shared pipeline (this *is* a pass-based restart with
start/end coordinates), just without the phase-based value model or any
type-specific extras of its own.

**Export to CSV/Excel**
   ``wa-setpieces workflow match.json --type goal_kick --format xlsx --output tables/``.

**Metrics to pull**
   Summary/counts, delivery locations, retention, first contacts, full
   routine taxonomy/clusters, defensive conceding summary. No
   second-phase detection or aerial-duel summary (corner/free-kick-only),
   and no goal-kick-specific extras the way throw-in has long throws or
   penalty has placement.

**Value model**
   Not available -- same reasoning as throw-in: no
   :class:`~wa_setpieces.XTModel` link for this type yet, so
   ``added_value``/``player_rating`` are ``None``. Team rating runs from
   success rate and retention rate.

**Visualisation**
   General plot set: :func:`~wa_setpieces.viz.plots.plot_delivery_map`,
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`,
   :func:`~wa_setpieces.viz.plots.plot_routine_clusters`,
   :func:`~wa_setpieces.viz.plots.plot_team_comparison`. No xT-based
   plots (needs the value model above).

.. _kick-off-coming-soon:

Kick off (coming soon)
-----------------------

Detected and extracted today -- the basics work now -- but without any
of the type-specific depth the other five have, so treat it as the
least mature category rather than "not implemented."

**What works today**
   Extraction (:func:`~wa_setpieces.extract_kick_offs`), summary/counts,
   delivery locations, retention, generic routine
   taxonomy/clusters, and CSV/Excel export -- all through the same
   ``run_workflow(events, "kick_off")`` / ``wa-setpieces workflow --type
   kick_off`` calls as every other type. General plots
   (:func:`~wa_setpieces.viz.plots.plot_delivery_map`,
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap`) render fine on it.

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
rate alone (see :doc:`user_guide/value_and_ratings`).
