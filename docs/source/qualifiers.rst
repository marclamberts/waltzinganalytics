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
   * - 223 / 224
     - In-swinger / Out-swinger
     - :func:`wa_setpieces.restart_routines`'s ``delivery_technique``
       column (``"inswinger"``/``"outswinger"``) for corners/free kicks --
       ``constants.QUALIFIER_INSWINGER``/``QUALIFIER_OUTSWINGER``. Confirmed
       mutually exclusive across every corner in the sample match.
   * - 102 / 103
     - Goal mouth Y / Z
     - :func:`wa_setpieces.core.placement.goal_placement` (shared by
       :mod:`wa_setpieces.ml.shot_value` and
       :func:`wa_setpieces.penalty_placement_detail`) for where in the goal
       frame a shot/penalty was placed. ``goal_y_norm`` is confirmed by its
       value range; ``goal_h_norm`` additionally assumes qualifier 103 is on
       a 0-38 scale (38 = crossbar), seen in other open-source Opta parsers
       but not independently confirmed here.
   * - 20 / 72
     - Right footed / Left footed
     - Body-part features in :mod:`wa_setpieces.ml.shot_value`
       (``QUALIFIER_RIGHT_FOOTED``/``QUALIFIER_LEFT_FOOTED``). **Not** swing
       direction -- an earlier version of this package's
       ``convert.corners``/``providers.statsbomb`` mistakenly used qualifier
       72 for "in-swinger" (they read the same numeric value, but 72 also
       appears on shot events, where swing direction is meaningless, and
       co-occurs with both 223 and 224 depending on which foot the taker
       used). Fixed to use 223 in both places.
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

Attempts/success counts in :mod:`wa_setpieces.core.metrics` use Opta's own
``outcome`` field on the restart event (``1`` = successful, ``0`` =
unsuccessful) as reported by the data provider -- e.g. for a throw-in this
usually means "won by the throwing team", and for a free kick/corner it
usually means "completed to a teammate". This package does not re-derive
outcome from subsequent possession; it reports what the feed says.

Don't confuse that raw ``outcome`` flag with ``delivery_outcome``, the
*classified* result column on :func:`wa_setpieces.delivery_outcomes` and
:func:`wa_setpieces.restart_routines` (``short_corner``/``aerial_duel``/
``goal``/``lost``/...) -- both were named ``category``/``outcome_category``
in earlier versions and were unified into ``delivery_outcome`` precisely
because that overlap with the raw flag was confusing.
