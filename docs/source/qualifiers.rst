Opta qualifier reference
=========================

The F24 feed does not give set pieces their own event type -- almost all of
them are ordinary pass events (``typeId == 1``) carrying a qualifier that
flags the restart type. Penalties are the exception: they are shot events
(miss/post/attempt-saved/goal) carrying a "Penalty" qualifier instead.

.. list-table::
   :header-rows: 1

   * - Set piece
     - Detected on
     - qualifierId
     - Constant
   * - Penalty
     - shot event (13/14/15/16)
     - 9
     - ``constants.QUALIFIER_PENALTY``
   * - Kick-off
     - pass event (1)
     - 279
     - ``constants.QUALIFIER_KICK_OFF``
   * - Free kick
     - pass event (1), corners excluded
     - 5
     - ``constants.QUALIFIER_FREE_KICK_TAKEN``
   * - Corner
     - pass event (1)
     - 6
     - ``constants.QUALIFIER_CORNER_TAKEN``
   * - Throw-in
     - pass event (1)
     - 107
     - ``constants.QUALIFIER_THROW_IN``
   * - Goal kick
     - pass event (1)
     - 124
     - ``constants.QUALIFIER_GOAL_KICK``

These are the standard Opta/Stats Perform F24 qualifier IDs. They were
cross-checked against a real match export (``tests/data/sample_match.json``):
every tagged event lines up with the pitch location you'd expect --
corner-qualifier events sit in the corner arc, throw-in events sit on the
touchline, kick-off events sit at the centre spot, and goal-kick events sit
on the six-yard line. See ``tests/test_filters.py`` for the assertions.

Other qualifiers used by this package
----------------------------------------

.. list-table::
   :header-rows: 1

   * - qualifierId
     - Meaning
     - Used for
   * - 55
     - Related event id
     - :func:`wa_setpieces.link_set_piece_shots` walks this from a shot
       back to its assisting pass to detect set-piece-created shots/goals.
   * - 140 / 141
     - Pass end X / end Y
     - :func:`wa_setpieces.delivery_locations` uses these for delivery
       maps (e.g. where a corner ended up).
   * - 123
     - Keeper throw
     - Not currently classified as a distinct set-piece type, but reserved
       as ``constants.QUALIFIER_KEEPER_THROW`` for callers who want to treat
       it separately from open play.
   * - 2
     - Cross
     - Reserved as ``constants.QUALIFIER_CROSS``; useful in combination with
       ``corner``/``free_kick`` tags to identify crossed set-piece deliveries.

A note on "success"
----------------------

Attempts/success counts in :mod:`wa_setpieces.metrics` use Opta's own
``outcome`` field on the restart event (``1`` = successful, ``0`` =
unsuccessful) as reported by the data provider -- e.g. for a throw-in this
usually means "won by the throwing team", and for a free kick/corner it
usually means "completed to a teammate". This package does not re-derive
outcome from subsequent possession; it reports what the feed says.
