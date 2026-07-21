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

Command line
-------------

.. code-block:: bash

   wa-setpieces match.json
   wa-setpieces match.json --csv summary.csv

Plotting
---------

``pip install "wa-setpieces[viz]"`` adds :mod:`wa_setpieces.viz.plots`,
pitch plots built on `mplsoccer <https://mplsoccer.readthedocs.io>`_ for
everything above -- delivery maps, zone heatmaps, second-phase sequences,
xT grids. See the :ref:`gallery` for the full set with source code.

.. code-block:: python

   from wa_setpieces.viz.plots import plot_delivery_map

   corners = delivery_locations(match.events, "corner")
   fig, ax = plot_delivery_map(corners, title="Corner deliveries")
