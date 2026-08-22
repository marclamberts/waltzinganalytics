Metrics, deliveries and zones
================================

The base layer: counts, delivery locations, and where on the pitch
things happened. Everything in :doc:`value_and_ratings` and
:doc:`routines` builds on top of what's here.

Team and player counts
-------------------------

.. code-block:: python

   from wa_setpieces import team_set_piece_counts, player_set_piece_counts

   team_set_piece_counts(match.events)
   player_set_piece_counts(match.events)

Both return attempts, successful attempts, and a success rate per
``(team, set_piece_type)`` or ``(player, set_piece_type)``. "Success"
follows Opta's own ``outcome`` flag on the restart event -- for a
throw-in this usually means "won by the throwing team," for a free kick
or corner it usually means "completed to a teammate." See :doc:`../qualifiers`'
"A note on success" for how that differs from ``delivery_outcome``.

Delivery locations
--------------------

For pass-based set pieces (corner, free kick, throw-in, goal kick, kick
off), :func:`~wa_setpieces.delivery_locations` returns start/end pitch
coordinates -- what a delivery map or heatmap is built from:

.. code-block:: python

   from wa_setpieces import delivery_locations

   corners = delivery_locations(match.events, "corner")
   # columns: eventId, contestantId, playerId, playerName, x, y, end_x, end_y, outcome

Linking to shots and goals
-----------------------------

:func:`~wa_setpieces.link_set_piece_shots` walks Opta's assist-chain
qualifier back from every shot (including goals) to the set piece that
created it, when one exists:

.. code-block:: python

   from wa_setpieces import link_set_piece_shots, set_piece_goal_summary

   link_set_piece_shots(match.events)
   set_piece_goal_summary(match.events)  # goals per team per set-piece type

.. important::

   Resolving "which shot did this delivery produce" this way -- rather
   than guessing from proximity in time -- mattered because of a real F24
   quirk: **eventId is only unique within one team's own event stream**.
   Both teams number their events 1, 2, 3, ... independently (confirmed
   against the sample match: 1464 of 1613 rows share an ``eventId`` with a
   same-numbered row from the *other* team). Anywhere this package resolves
   one event by ``eventId``, the lookup is scoped to a team first -- an
   unscoped ``events[events["eventId"] == x]`` on the raw feed is not safe.

The all-in-one summary
-------------------------

:func:`~wa_setpieces.set_piece_summary` combines the above into one
headline table: attempts, success rate, shots and goals, per team, for
every set-piece type at once. This is usually the first call you make on
a new match -- see the :doc:`../quickstart`.

.. code-block:: python

   from wa_setpieces import set_piece_summary

   set_piece_summary(match.events)

Zones, thirds and channels
-----------------------------

:mod:`wa_setpieces.core.zones` classifies pitch location using the
confirmed F24 convention that every event's ``x``/``y`` are in *that
event's own team's* attacking direction (``x=0`` own goal, ``x=100``
opponent's goal -- see the module docstring for how this was verified
against the sample match).

.. code-block:: python

   from wa_setpieces import add_thirds, add_channels, add_zone_grid, zone_counts

   tagged = add_thirds(match.events)   # "defensive_third" / "middle_third" / "attacking_third"
   tagged = add_channels(tagged, n=5)  # wide / half-space / central (or n=3 for left/central/right)
   tagged = add_zone_grid(tagged)      # 6x3 = 18-zone grid label, e.g. "R1C4"

   zone_counts(match.events, group_cols=["contestantId"])  # heatmap-ready counts per zone per team

Apply these to :func:`~wa_setpieces.delivery_locations` output to see
which channel or third corners and free kicks are delivered *into*:

.. code-block:: python

   from wa_setpieces import delivery_locations
   from wa_setpieces.core.zones import add_channels

   corners = delivery_locations(match.events, "corner")
   corners_end = add_channels(corners, y_col="end_y", n=5)
   corners_end["channel"].value_counts()

:func:`~wa_setpieces.viz.plots.plot_zone_heatmap` (see :doc:`visualisation`)
turns any of these zone counts straight into a pitch heatmap.
