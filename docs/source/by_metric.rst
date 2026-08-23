.. _by-metric:

By metric
============

The same pick-one-see-what-it-does reference :doc:`categories` gives set
pieces and :doc:`value_models` gives value models, for the base metrics
layer -- counts, delivery locations, shot/goal linking, the all-in-one
summary, and pitch zones.

Team and player counts
---------------------------

**What it returns**
   Attempts, successful attempts, and a success rate per
   ``(team, set_piece_type)`` or ``(player, set_piece_type)``. "Success"
   follows Opta's own ``outcome`` flag on the restart event as reported
   by the provider -- this package doesn't re-derive success from
   subsequent possession. Don't confuse this with ``delivery_outcome``
   (see :doc:`by_phase`), a separately classified result column.

**Requirements**
   Just an events frame -- works on any set-piece type, no model needed.

**Compute it**

.. code-block:: python

   from wa_setpieces import team_set_piece_counts, player_set_piece_counts

   team_set_piece_counts(events)
   player_set_piece_counts(events)

**Where it's used**
   The team-count rows feed :func:`~wa_setpieces.set_piece_summary`
   below; both are the base of every per-category breakdown in
   :doc:`categories`.

Delivery locations
----------------------

**What it returns**
   Start/end pitch coordinates for one pass-based set-piece type --
   ``eventId``, ``contestantId``, ``playerId``, ``playerName``, ``x``,
   ``y``, ``end_x``, ``end_y``, ``outcome``. What a delivery map or
   heatmap is built from.

**Requirements**
   A pass-based type: ``corner``, ``free_kick``, ``throw_in``,
   ``goal_kick`` or ``kick_off`` -- not ``penalty`` (a shot, no
   delivery coordinates; see :doc:`by_routine`'s penalty-placement
   entry instead).

**Compute it**

.. code-block:: python

   from wa_setpieces import delivery_locations

   corners = delivery_locations(events, "corner")

**Where it's used**
   :func:`~wa_setpieces.viz.plots.plot_delivery_map` and every other
   pitch plot in the :ref:`gallery`; the zone functions below.

Linking to shots and goals
-------------------------------

**What it returns**
   Every shot (including goals) traced back to the set piece that
   created it, via Opta's own assist-chain qualifier -- not a
   positional guess.

**Requirements**
   Just an events frame.

**Compute it**

.. code-block:: python

   from wa_setpieces import link_set_piece_shots, set_piece_goal_summary

   link_set_piece_shots(events)     # every shot, tagged with its originating set piece
   set_piece_goal_summary(events)   # goals per team per set-piece type

.. important::

   The feed's ``eventId`` is only unique *within one team's own event stream* --
   both teams number their events 1, 2, 3, ... independently. This
   function scopes its lookup to a team first; an unscoped
   ``events[events["eventId"] == x]`` on the raw feed is not safe.

**Where it's used**
   :func:`~wa_setpieces.core.value.set_piece_added_value` (:doc:`value_models`)
   resolves "did this delivery produce a shot" the same way.

The all-in-one summary
----------------------------

**What it returns**
   One headline table: attempts, success rate, shots and goals, per
   team, for every set-piece type at once -- usually the first call on
   a new match.

**Requirements**
   Just an events frame.

**Compute it**

.. code-block:: python

   from wa_setpieces import set_piece_summary

   set_piece_summary(events)

**Where it's used**
   The :doc:`quickstart`'s first real call; ``wa-setpieces match.json``
   on the command line runs this directly.

Zones, thirds and channels
-------------------------------

**What it returns**
   Pitch-location labels added to any frame with ``x``/``y`` columns:
   thirds (defensive/middle/attacking), channels (wide/half-space/central,
   or a coarser left/central/right), an 18-cell zone grid, and
   heatmap-ready per-zone counts.

**Requirements**
   Any frame with ``x``/``y`` (or ``end_x``/``end_y``, via the
   ``x_col``/``y_col`` args) -- raw events or
   :func:`~wa_setpieces.delivery_locations` output both work.

**Compute it**

.. code-block:: python

   from wa_setpieces import add_thirds, add_channels, add_zone_grid, zone_counts, delivery_locations

   tagged = add_thirds(events)            # "defensive_third" / "middle_third" / "attacking_third"
   tagged = add_channels(tagged, n=5)            # wide / half-space / central
   tagged = add_zone_grid(tagged)                # 6x3 = 18-zone grid label, e.g. "R1C4"

   zone_counts(events, group_cols=["contestantId"])  # per-zone counts per team

   corners = add_channels(delivery_locations(events, "corner"), y_col="end_y", n=5)
   corners["channel"].value_counts()             # which channel corners are delivered *into*

**Where it's used**
   :func:`~wa_setpieces.viz.plots.plot_zone_heatmap` in the
   :ref:`gallery`; the free-kick/corner origin-zone features in
   :doc:`by_routine`.
