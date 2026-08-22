Second phases, retention and outcomes
========================================

Three questions the raw qualifiers can't answer directly: *did the
danger continue* after the first contact, *did the team keep the ball*,
and *what, exactly, happened* to each delivery. All three are **derived
heuristics** layered on top of the F24 feed, not fields the provider
gives you -- read each section's caveats before relying on the numbers.

Second phases
----------------

:mod:`wa_setpieces.core.phases` walks forward from every corner/free-kick
delivery and classifies what happened: did the defence clear it
immediately, was there a shot straight off the delivery, or did the ball
stay alive (a knockdown, blocked clearance, loose ball) long enough for
the attacking team to get a **second-phase shot** away.

.. code-block:: python

   from wa_setpieces import second_phases, second_phase_summary

   second_phases(match.events, "corner")         # one row per corner, with the classification
   second_phase_summary(match.events, "corner")  # per-team roll-up: deliveries, second phases, goals

There is no "phase" field in F24, so this is inferred from event
sequencing -- time gaps, who touches the ball, whether a defensive
clearance travels far enough up the pitch. The thresholds are tunable:

.. code-block:: python

   from wa_setpieces.core.phases import second_phases

   second_phases(
       match.events, "corner",
       clear_safe_x=40,       # how far up the pitch a clearance must travel to count as "cleared"
       max_gap_seconds=6,     # a bigger gap between events ends the phase window
       max_total_seconds=15,  # hard cap on how long after the delivery we keep looking
   )

Only corners and free kicks get this treatment -- see :doc:`../categories`'
coverage matrix for which types have second-phase detection.

Retention
------------

A broader question than the raw pass ``outcome`` flag: did the team that
took the set piece still have the ball some seconds later (default 8s),
regardless of whether the very first pass found a teammate.

.. code-block:: python

   from wa_setpieces import retention_detail, retention_rate

   retention_detail(match.events, "corner")   # per-delivery: outcome vs. retained
   retention_rate(match.events, "throw_in")   # per-team retention rate
   retention_rate(match.events, "corner", window_seconds=5)

Works for ``kick_off``, ``free_kick``, ``corner``, ``throw_in`` and
``goal_kick``. Penalties are excluded -- a penalty is a single shot, not a
restart with a meaningful "possession after" question.

Outcomes and aerial duels
-----------------------------

:mod:`wa_setpieces.core.outcomes` builds on second-phase detection above
and classifies every corner/free-kick delivery into one discrete
``delivery_outcome`` -- for a shot-map-style scatter
(:func:`~wa_setpieces.viz.plots.plot_set_piece_outcomes`, see
:doc:`visualisation`):

.. code-block:: python

   from wa_setpieces import delivery_outcomes, outcome_summary

   delivery_outcomes(match.events, "corner")  # one row per delivery
   outcome_summary(match.events, "corner")    # per-team counts of each category

``delivery_outcome`` is one of ``short_corner``, ``direct_shot``,
``second_phase_shot``, ``aerial_duel``, ``cleared``, ``first_touch_won``,
``first_touch_lost`` or ``no_action`` -- categories are checked in that
priority order per delivery; see the module docstring for exactly which
event each category's plotted location comes from.

.. note::

   Before 0.17.0 this column was named ``category`` here and
   ``outcome_category`` on :func:`~wa_setpieces.restart_routines` -- both
   renamed to ``delivery_outcome`` for consistency, and to read distinctly
   from the raw pass/shot success ``outcome`` flag they sit next to in the
   same tables (see :doc:`../qualifiers`).

When the outcome is ``"aerial_duel"``, the raw Opta Aerial event's own
``outcome`` flag identifies who actually won that header (Opta logs one
Aerial event per team involved, confirmed as a matched winner/loser pair
against the sample match) -- exposed both per-delivery
(``aerial_winner_contestant_id``/``_player_id``/``_player_name`` columns on
``delivery_outcomes``) and rolled up:

.. code-block:: python

   from wa_setpieces import aerial_duel_summary

   team_summary, player_summary = aerial_duel_summary(match.events, "corner")
   # team_summary: duels_involved, duels_won, win_rate, per team
   # player_summary: duels_won per player with at least one *identified* win
   # (a loss identifies the winning team but not the winning player, since
   # only the loser's own event is what's being read)
