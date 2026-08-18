Quickstart
==========

Loading a match
----------------

:func:`wa_setpieces.load_events` reads an F24 JSON file (or an already
parsed ``dict``) and returns a :class:`~wa_setpieces.core.loader.Match`
containing the raw ``matchDetails`` block and a tidy events
:class:`pandas.DataFrame` (one row per event, one column per qualifierId,
named ``q_<id>``).

.. code-block:: python

   from wa_setpieces import load_events

   match = load_events("match.json")
   match.events.head()

Got more than one match? :func:`~wa_setpieces.load_events_multi` loads and
stacks several exports into one events DataFrame (tagged with a
``matchId`` column) for season-level aggregation -- see the "Multiple
matches" section on the :doc:`advanced` page for what that is and isn't
safe to use for.

The whole pipeline in one call
---------------------------------

Everything on this page below -- team/player counts, delivery locations,
second-phase detection, retention, added value, the report, the rating,
defensive conceding profiles, routine clusters, aerial-duel record,
penalty placement, and long-throw analysis -- is one function chain most
people want run together. :func:`~wa_setpieces.run_workflow` runs that
whole chain for one set-piece type and hands back every table in one
:class:`~wa_setpieces.core.workflow.SetPieceWorkflow`:

.. code-block:: python

   from wa_setpieces import run_workflow, XTModel

   model = XTModel.fit(match.events)  # optional -- unlocks added value + player rating
   result = run_workflow(match.events, "corner", model=model)

   result.summary                     # attempts, success rate, shots, goals
   result.deliveries                  # start/end coordinates for a delivery map
   result.second_phases               # cleared / first-phase shot / second-phase shot
   result.retention                   # still in possession ~8s later?
   result.added_value                 # xT added + resulting shot quality + goals, per delivery
   result.report                      # all of the above, rolled up per team
   result.team_rating                 # 0-100 benchmark score per team
   result.player_rating               # delivery score / finishing score per player
   result.defensive_summary           # attempts/shots/goals conceded, per team
   result.defensive_routine_summary   # what a team concedes most, by routine type
   result.defensive_zone_summary      # ... by destination zone
   result.routine_clusters            # data-driven (k-means) delivery clusters (needs the ml extra)
   result.aerial_duel_team_summary    # aerial-duel win rate per team
   result.aerial_duel_player_summary  # aerial-duel wins per player

Set ``set_piece_type`` to ``"penalty"`` or ``"throw_in"`` to also get
``result.penalty_placement``/``penalty_taker_summary`` or
``result.long_throw_taker_summary``/``long_throw_second_phases``
respectively.

Fields that don't apply to the set-piece type you asked for (e.g.
``deliveries`` for ``"penalty"``, or anything needing ``model`` when none
was passed), or that need an optional extra that isn't installed
(``routine_clusters`` needs the ``ml`` extra's scikit-learn), are
``None`` rather than an empty table. The rest of this page walks through
each of those pieces individually -- reach for the individual functions
directly when you only need one, want different parameters per step, or
are combining several matches.

Loading data from other providers
------------------------------------

Opta F24 is the native format, handled directly above. StatsBomb open-data
exports go through an adapter first --
:func:`~wa_setpieces.load_statsbomb_events` converts them into the same
internal events DataFrame, so every function on this page works unchanged
on either source:

.. code-block:: python

   from wa_setpieces import load_statsbomb_events

   events = load_statsbomb_events("statsbomb_events_export.json")
   set_piece_summary(events)

See :mod:`wa_setpieces.providers.statsbomb`'s module docstring for exactly
what is (and isn't) faithfully mapped.

Extracting set pieces
----------------------

Each set-piece type has a dedicated extractor that filters the events
DataFrame down to just that restart:

.. code-block:: python

   from wa_setpieces import (
       extract_corners, extract_free_kicks, extract_throw_ins,
       extract_goal_kicks, extract_kick_offs, extract_penalties,
       extract_all,
   )

   corners = extract_corners(match.events)
   all_set_pieces = extract_all(match.events)  # dict: name -> DataFrame

To label every event in place instead, use :func:`~wa_setpieces.tag_set_pieces`,
which adds a ``set_piece_type`` column (``None`` for non-set-piece events):

.. code-block:: python

   from wa_setpieces import tag_set_pieces

   tagged = tag_set_pieces(match.events)
   tagged[tagged["set_piece_type"] == "corner"]

Team and player metrics
------------------------

.. code-block:: python

   from wa_setpieces import team_set_piece_counts, player_set_piece_counts

   team_set_piece_counts(match.events)
   player_set_piece_counts(match.events)

Both return attempts, successful attempts, and a success rate per
``(team, set_piece_type)`` or ``(player, set_piece_type)``. "Success" follows
Opta's own ``outcome`` flag on the restart event (e.g. for a throw-in,
whether possession was retained).

Delivery locations
--------------------

For pass-based set pieces (corner, free kick, throw-in, goal kick, kick off),
:func:`~wa_setpieces.delivery_locations` returns start/end pitch
coordinates -- handy for corner maps or throw-in heatmaps:

.. code-block:: python

   from wa_setpieces import delivery_locations

   corners = delivery_locations(match.events, "corner")
   # columns: eventId, contestantId, playerId, playerName, x, y, end_x, end_y, outcome

Linking set pieces to shots and goals
---------------------------------------

:func:`~wa_setpieces.link_set_piece_shots` walks Opta's assist-chain
qualifier back from every shot (including goals) to the set piece that
created it, when one exists:

.. code-block:: python

   from wa_setpieces import link_set_piece_shots, set_piece_goal_summary

   link_set_piece_shots(match.events)
   set_piece_goal_summary(match.events)  # goals per team per set-piece type

The all-in-one summary
-------------------------

:func:`~wa_setpieces.set_piece_summary` combines the above into one
headline table: attempts, success rate, shots, and goals per team per
set-piece type.

.. code-block:: python

   from wa_setpieces import set_piece_summary

   set_piece_summary(match.events)

Ratings
--------

:mod:`wa_setpieces.core.rating` turns a report into a single 0-100 "how
good" score, benchmarked against whoever else is in the table -- always
rate a full season/competition, not one match (see the module docstring
for why).

.. code-block:: python

   from wa_setpieces import team_rating, player_rating

   team_rating(corner_report(season_events, model=model))
   player_rating(season_events, "corner", model, min_deliveries=5, min_shots=3)

Routines: technique, target and clusters
--------------------------------------------

:func:`~wa_setpieces.restart_routines` describes *how* a restart was
taken -- distance, direction, a rule-based routine taxonomy, and (for
corners/free kicks) ``delivery_technique`` (``"inswinger"``/``"outswinger"``,
from Opta qualifiers 223/224) and ``post_target``
(``"near_post"``/``"far_post"``/``"central"``, relative to which flank
the restart was taken from):

.. code-block:: python

   from wa_setpieces import restart_routines, routine_summary, analyze_routines

   restart_routines(match.events, "corner")
   analyze_routines(match.events, "corner", min_taker_attempts=3)
   # .detail / .summary / .team_profiles / .taker_profiles / .target_matrix

As a data-driven alternative to that fixed taxonomy,
:func:`~wa_setpieces.cluster_routines` groups deliveries by geometric
similarity (k-means) instead:

.. code-block:: python

   from wa_setpieces import cluster_routines, cluster_summary

   clustered = cluster_routines(match.events, "corner", n_clusters=5)  # needs the ml extra
   cluster_summary(clustered)

Long throws and penalties have their own dedicated helpers --
:func:`~wa_setpieces.long_throw_taker_summary`/
:func:`~wa_setpieces.long_throw_second_phases` for the one throw-in
pattern that plays like a corner, and
:func:`~wa_setpieces.penalty_placement_detail`/
:func:`~wa_setpieces.penalty_taker_summary` for penalty placement zone
and per-taker conversion. See :doc:`advanced` for both.

Outcomes and aerial duels
-----------------------------

:func:`~wa_setpieces.delivery_outcomes` classifies each corner/free-kick
delivery into one discrete ``delivery_outcome`` for a shot-map-style
scatter -- and, when that outcome is a contested header,
:func:`~wa_setpieces.aerial_duel_summary` reports who actually won it:

.. code-block:: python

   from wa_setpieces import delivery_outcomes, outcome_summary, aerial_duel_summary

   delivery_outcomes(match.events, "corner")
   # delivery_outcome: short_corner / direct_shot / second_phase_shot / aerial_duel /
   # cleared / first_touch_won / first_touch_lost / no_action

   team_summary, player_summary = aerial_duel_summary(match.events, "corner")

Defending and opponent scouting
------------------------------------

:mod:`wa_setpieces.core.defending` flips the attacking-team perspective
to "what does this team concede":

.. code-block:: python

   from wa_setpieces import defensive_set_piece_summary, defensive_routine_summary

   defensive_set_piece_summary(match.events)          # attempts/shots/goals conceded
   defensive_routine_summary(match.events, "corner")  # ... by routine type conceded

:func:`~wa_setpieces.opponent_scouting_report_html` turns that into a
ready-to-view pre-match scouting report for one opponent -- see
:doc:`advanced`.

Season form and exporting
------------------------------

:class:`~wa_setpieces.SeasonDataset` (see "Multiple matches" on
:doc:`advanced`) adds rolling attacking *and* defensive form on top of
its season-safe aggregation:

.. code-block:: python

   from wa_setpieces import SeasonDataset

   season = SeasonDataset.from_sources(match_files)  # already in chronological order
   season.rolling_summary(window=5)            # rolling attacking form
   season.rolling_defensive_summary(window=5)  # rolling defensive form

Any table this package produces can be saved to CSV or Excel:

.. code-block:: python

   from wa_setpieces import save_table

   save_table(corner_report(match.events, model=model), "corner_report.xlsx")  # needs the xlsx extra

Command line
-------------

.. code-block:: bash

   wa-setpieces match.json
   wa-setpieces match.json --csv summary.csv

The ``workflow``/``report`` subcommands export the full
:func:`~wa_setpieces.run_workflow` output -- every table above, including
the defensive, routine-cluster, aerial-duel, penalty and long-throw
tables -- with no extra flags needed:

.. code-block:: bash

   wa-setpieces workflow match.json --type corner --model league-model.npz --output tables/
   wa-setpieces report match.json --type corner --model league-model.npz --output report.html

Plotting
---------

``pip install "wa-setpieces[viz]"`` adds :mod:`wa_setpieces.viz.plots`,
pitch plots built on `mplsoccer <https://mplsoccer.readthedocs.io>`_ for
everything above -- delivery maps, zone heatmaps, second-phase sequences,
xT grids, a rating benchmark chart, routine clusters, defensive conceding
bars, and aerial-duel win rate. See the :ref:`gallery` for the full set
with source code.

.. code-block:: python

   from wa_setpieces.viz.plots import plot_delivery_map

   corners = delivery_locations(match.events, "corner")
   fig, ax = plot_delivery_map(corners, title="Corner deliveries")
