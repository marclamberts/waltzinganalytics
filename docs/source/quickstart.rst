Quickstart
==========

This walks through one match end to end: load it, summarize it, plot it.
Five minutes, no data of your own required -- the package ships a real
(anonymized) match export for exactly this.

Load a match
------------

:func:`~wa_setpieces.load_events` reads an Opta JSON file and returns a
:class:`~wa_setpieces.core.loader.Match`: the raw ``matchDetails`` block,
plus a tidy events :class:`pandas.DataFrame` -- one row per event, one
column per qualifierId, named ``q_<id>``.

.. code-block:: python

   from wa_setpieces import load_events

   match = load_events("tests/data/sample_match.json")
   match.events.head()

On StatsBomb or IMPECT data instead, or a whole season rather than one
match? :func:`~wa_setpieces.load_matches` handles a single file or a
folder for any of the three providers -- ``load_matches("match.json",
provider="statsbomb")`` -- and returns the same events shape either way,
so every example below works unchanged regardless of source. See
:doc:`installation`'s "Input data" section for the full picture.

Summarize every set piece
--------------------------

:func:`~wa_setpieces.set_piece_summary` is the one-call headline table:
attempts, success rate, shots and goals, per team, for all six set-piece
types at once.

.. code-block:: python

   from wa_setpieces import set_piece_summary

   set_piece_summary(match.events)

.. code-block:: text

               contestantId set_piece_type  attempts  successful  success_rate  shots  goals
   cxb4hqite921i...      corner         2           1         0.500      0      0
   cxb4hqite921i...   free_kick        12           9         0.750      0      0
   cxb4hqite921i...   goal_kick         8           5         0.625      0      0
   cxb4hqite921i...    kick_off         1           1         1.000      0      0
   cxb4hqite921i...    throw_in        20          16         0.800      0      0
   f2yd0yzt0om6q...      corner         7           1         0.143      0      0
   f2yd0yzt0om6q...   free_kick        13           9         0.692      0      0
   f2yd0yzt0om6q...   goal_kick         4           3         0.750      0      0
   f2yd0yzt0om6q...    kick_off         3           3         1.000      0      0
   f2yd0yzt0om6q...    throw_in        30          27         0.900      0      0

Plot the deliveries
--------------------

:func:`~wa_setpieces.delivery_locations` pulls out start/end pitch
coordinates for one set-piece type; :func:`~wa_setpieces.viz.plots.plot_delivery_map`
(needs the ``viz`` extra) draws it on an mplsoccer pitch.

.. code-block:: python

   from wa_setpieces import delivery_locations
   from wa_setpieces.viz.plots import plot_delivery_map

   corners = delivery_locations(match.events, "corner")
   fig, ax = plot_delivery_map(corners, title="Corner deliveries")

.. image:: _static/hero_corners.png
   :alt: Corner delivery map drawn with mplsoccer
   :align: center
   :width: 560px

Run the whole pipeline
------------------------

Everything past a summary table -- second-phase detection, retention,
an xT-based added-value score, a 0-100 rating, routine taxonomy,
defensive conceding, aerial duels -- is one more call:
:func:`~wa_setpieces.run_workflow` runs the full chain for one
set-piece type and hands back every table in a single
:class:`~wa_setpieces.core.workflow.SetPieceWorkflow`.

.. code-block:: python

   from wa_setpieces import run_workflow, XTModel

   model = XTModel.fit(match.events)  # optional -- unlocks added value + player rating
   result = run_workflow(match.events, "corner", model=model)

   result.report          # everything above, rolled up per team
   result.team_rating      # 0-100 benchmark score per team
   result.player_rating    # delivery score / finishing score per player

.. note::

   Fitting :class:`~wa_setpieces.XTModel` on one match, as above, is
   illustrative only -- it's nowhere near enough data for a trustworthy
   grid. Fit across a season instead; see :doc:`value_models`.

The same thing from the command line:

.. code-block:: bash

   wa-setpieces workflow tests/data/sample_match.json --type corner --output tables/ --format xlsx

Where next
-----------

- :doc:`categories` -- already know which set piece you care about?
  Corner, free kick, throw-in, penalty, goal kick or kick-off: see
  exactly what's available for it.
- :doc:`value_models` -- already know which value model you care about?
  xT, added value, shot value, team/player/defensive rating: see what
  each one measures and how to compute it.
- :doc:`by_metric`, :doc:`by_phase`, :doc:`by_routine`, :doc:`by_report`
  -- the same pick-one-see-how-it-works reference for metrics/zones,
  phases/outcomes, routines, and reporting/export.
- :doc:`gallery/index` -- every plot this package makes, with the source
  code that made it.
