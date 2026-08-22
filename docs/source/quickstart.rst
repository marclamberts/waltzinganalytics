Quickstart
==========

This walks through one match end to end: load it, summarize it, plot it.
Five minutes, no data of your own required -- the package ships a real
(anonymized) F24 match export for exactly this.

Load a match
------------

:func:`~wa_setpieces.load_events` reads an F24 JSON file and returns a
:class:`~wa_setpieces.core.loader.Match`: the raw ``matchDetails`` block,
plus a tidy events :class:`pandas.DataFrame` -- one row per event, one
column per qualifierId, named ``q_<id>``.

.. code-block:: python

   from wa_setpieces import load_events

   match = load_events("tests/data/sample_match.json")
   match.events.head()

On StatsBomb data instead? :func:`~wa_setpieces.load_statsbomb_events`
converts a StatsBomb open-data export into the same events frame, so
every example below works unchanged on either source -- see
:doc:`user_guide/loading`.

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
   cxb4hqite921i...      corner         2           1         0.500      1      0
   cxb4hqite921i...   free_kick        12           9         0.750      0      0
   cxb4hqite921i...   goal_kick         8           5         0.625      0      0
   cxb4hqite921i...    kick_off         1           1         1.000      0      0
   cxb4hqite921i...    throw_in        20          16         0.800      1      0

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
   grid. Fit across a season instead; see :doc:`user_guide/value_and_ratings`.

The same thing from the command line:

.. code-block:: bash

   wa-setpieces workflow tests/data/sample_match.json --type corner --output tables/ --format xlsx

Where next
-----------

- :doc:`categories` -- already know which set piece you care about?
  Corner, free kick, throw-in, penalty, goal kick or kick-off: see
  exactly what's available for it.
- :doc:`user_guide/index` -- the full tour: metrics, the xT value model,
  ratings, routines, defending, season form, reports and export.
- :doc:`gallery/index` -- every plot this package makes, with the source
  code that made it.
- :doc:`qualifiers` -- which Opta qualifierId backs every column this
  package derives.
