Routines, long throws and penalties
======================================

Everything so far describes *what happened*. This page describes *how
the restart was taken* -- a rule-based taxonomy, a data-driven
alternative, and two type-specific layers (throw-ins, penalties) that
don't fit the general shape. Already know which of these you want, and
just need the how-to? :doc:`../by_routine` covers the same ground
organized routine-by-routine instead of narratively.

Routine taxonomy
--------------------

:func:`~wa_setpieces.restart_routines` gives every delivery a rule-based
``routine_type`` (short / central-six-yard / penalty-area / recycled /
deep for corners, and an equivalent taxonomy per set-piece type -- see
the :mod:`wa_setpieces.core.routines` module docstring for the full
list), plus geometry (distance, angle, progression, verticality,
side/third/channel) and a stable ``routine_key``.

For corners and free kicks specifically, it also adds:

- ``delivery_technique`` -- ``"inswinger"``/``"outswinger"``, from Opta
  qualifiers 223/224 (see :doc:`../qualifiers` for why this isn't
  qualifier 72).
- ``post_target`` -- ``"near_post"``/``"far_post"``/``"central"``,
  relative to which flank the restart was taken from (the goalpost on
  the same side as the delivery's own start ``y`` is "near").

.. code-block:: python

   from wa_setpieces import restart_routines, analyze_routines

   restart_routines(match.events, "corner")
   analyze_routines(match.events, "corner", min_taker_attempts=3)
   # .detail / .summary / .team_profiles / .taker_profiles / .target_matrix

Data-driven clusters
------------------------

As an alternative to that fixed, hand-picked taxonomy,
:func:`~wa_setpieces.cluster_routines` groups deliveries by geometric
similarity instead (k-means over start/end x/y by default), surfacing
whatever patterns a team actually repeats rather than the patterns this
package's authors happened to name:

.. code-block:: python

   from wa_setpieces import cluster_routines, cluster_summary

   clustered = cluster_routines(match.events, "corner", n_clusters=5)  # needs the ml extra
   # restart_routines' detail plus `cluster` (int, -1 = unclustered) and
   # an auto-generated `cluster_label` (e.g. "short, forward, central")
   cluster_summary(clustered)  # per-cluster usage/outcome roll-up

:func:`~wa_setpieces.viz.plots.plot_routine_clusters` (see
:doc:`visualisation`) plots these clusters straight onto a pitch, one
color per cluster.

Long throws
--------------

The one throw-in pattern that plays like a corner -- a direct ball into
a crowded box, where a genuine long-throw specialist is a real tactical
weapon:

.. code-block:: python

   from wa_setpieces import long_throw_taker_summary, long_throw_second_phases

   long_throw_taker_summary(match.events, min_distance=25.0)
   # per-player usage share and threat created (shots/goals via the
   # assist-chain link) among throw-ins that travel at least min_distance

   long_throw_second_phases(match.events, min_distance=25.0)
   # event-sequence-based flick-on/knockdown detection (reuses the same
   # phase classifier as corners), restricted to those same long throws --
   # most throw-ins are a midfield restart with no "did this produce a
   # shot" question worth asking, unlike a corner

Penalties: placement
------------------------

Penalties are shots, not passes -- detected on shot events (see
:doc:`../qualifiers`), with ``restart_routines``' ``routine_type`` for
them just the shot result (scored/saved/post/missed).
:mod:`wa_setpieces.core.penalties` adds *where in the goal* each penalty
was placed, reusing the same goal-mouth-qualifier geometry
:mod:`wa_setpieces.ml.shot_value`'s shot-value models were built on --
pure geometry, no optional dependency needed:

.. code-block:: python

   from wa_setpieces import penalty_placement_detail, penalty_taker_summary

   penalty_placement_detail(match.events)
   # per-penalty result plus goal_y_norm/goal_h_norm (0-1 across/up the
   # frame), corner_zone (0-8, a 3x3 grid), placement_score (distance
   # from center -- corners of the frame score higher)

   penalty_taker_summary(match.events)
   # per-taker attempts, result breakdown, conversion rate, avg placement score
