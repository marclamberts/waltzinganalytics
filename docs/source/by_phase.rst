.. _by-phase:

By phase and outcome
========================

The same pick-one-see-what-it-does reference :doc:`categories` gives set
pieces, for the three questions the raw qualifiers can't answer directly:
*did the danger continue*, *did the team keep the ball*, and *what
exactly happened*. All three are **derived heuristics**, not fields the
provider gives you -- see each entry's caveats. The narrative version of
this material is :doc:`user_guide/phases_and_outcomes`.

Second phases
-----------------

**What it detects**
   Whether a corner/free-kick delivery was cleared immediately, produced
   a shot straight off the ball, or stayed alive (a knockdown, blocked
   clearance, loose ball) long enough for a **second-phase shot**.

**Requirements**
   ``corner`` or ``free_kick`` only -- inferred from event sequencing
   (time gaps, who touches the ball, clearance distance), so there's no
   equivalent for pass-based types without a meaningful "phase" concept.

**Compute it**

.. code-block:: python

   from wa_setpieces import second_phases, second_phase_summary

   second_phases(match.events, "corner")          # one row per corner, classified
   second_phase_summary(match.events, "corner")   # per-team roll-up

   # thresholds are tunable:
   from wa_setpieces.core.phases import second_phases as _second_phases
   _second_phases(match.events, "corner", clear_safe_x=40, max_gap_seconds=6, max_total_seconds=15)

**Where it's used**
   :func:`~wa_setpieces.core.value.set_piece_added_value` (:doc:`value_models`)
   and :func:`~wa_setpieces.viz.plots.plot_second_phase` in the
   :ref:`gallery`.

Retention
-------------

**What it detects**
   Whether the team that took the set piece still had the ball some
   seconds later (default 8s) -- a broader question than the raw pass
   ``outcome`` flag, which only checks whether the very first pass found
   a teammate.

**Requirements**
   Any type except ``penalty`` (a penalty is a single shot, not a
   restart with a meaningful "possession after" question).

**Compute it**

.. code-block:: python

   from wa_setpieces import retention_detail, retention_rate

   retention_detail(match.events, "corner")               # per-delivery: outcome vs. retained
   retention_rate(match.events, "throw_in")                # per-team retention rate
   retention_rate(match.events, "corner", window_seconds=5)

**Where it's used**
   ``set_piece_report``'s ``retention_rate`` column, which
   :func:`~wa_setpieces.team_rating` (:doc:`value_models`) uses for the
   four types with no xT path.

Outcomes
------------

**What it detects**
   One discrete ``delivery_outcome`` per corner/free-kick delivery --
   ``short_corner``, ``direct_shot``, ``second_phase_shot``,
   ``aerial_duel``, ``cleared``, ``first_touch_won``,
   ``first_touch_lost`` or ``no_action`` -- checked in that priority
   order, for a shot-map-style scatter.

**Requirements**
   ``corner`` or ``free_kick`` only -- builds on second-phase detection
   above.

**Compute it**

.. code-block:: python

   from wa_setpieces import delivery_outcomes, outcome_summary

   delivery_outcomes(match.events, "corner")  # one row per delivery
   outcome_summary(match.events, "corner")    # per-team counts of each category

.. note::

   Don't confuse ``delivery_outcome`` (this classified result) with the
   raw pass/shot ``outcome`` flag :doc:`by_metric`'s team/player counts
   use -- both were named ``category``/``outcome_category`` in earlier
   versions and were unified precisely because the overlap was
   confusing. See :doc:`qualifiers`.

**Where it's used**
   :func:`~wa_setpieces.viz.plots.plot_set_piece_outcomes` in the
   :ref:`gallery`; the aerial-duel entry below.

Aerial duels
----------------

**What it detects**
   When a delivery's outcome is ``"aerial_duel"``, who actually won the
   header -- from the raw Opta Aerial event's own ``outcome`` flag (Opta
   logs one Aerial event per team involved).

**Requirements**
   ``corner`` or ``free_kick`` only, same as the outcome classification
   it builds on.

**Compute it**

.. code-block:: python

   from wa_setpieces import aerial_duel_summary

   team_summary, player_summary = aerial_duel_summary(match.events, "corner")
   # team_summary: duels_involved, duels_won, win_rate, per team
   # player_summary: duels_won per player with at least one *identified* win
   # (a loss identifies the winning team but not the winning player --
   #  only the loser's own event is what's being read)

**Where it's used**
   :func:`~wa_setpieces.viz.plots.plot_aerial_duel_win_rate` in the
   :ref:`gallery`.
