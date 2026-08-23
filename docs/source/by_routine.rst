.. _by-routine:

By routine
=============

The same pick-one-see-what-it-does reference :doc:`categories` gives set
pieces, for the layer that describes *how* a restart was taken -- a
rule-based taxonomy, a data-driven alternative, and two type-specific
layers (throw-ins, penalties) that don't fit the general shape.

Routine taxonomy
---------------------

**What it describes**
   A rule-based ``routine_type`` per delivery (short / central-six-yard /
   penalty-area / recycled / deep for corners, an equivalent taxonomy per
   type), plus geometry (distance, angle, progression, side/third/channel)
   and a stable ``routine_key``. For corners/free kicks specifically:
   ``delivery_technique`` (``"inswinger"``/``"outswinger"``, from Opta
   qualifiers 223/224) and ``post_target``
   (``"near_post"``/``"far_post"``/``"central"``).

**Requirements**
   Any set-piece type -- works generically, with extra columns unlocked
   for corner/free kick.

**Compute it**

.. code-block:: python

   from wa_setpieces import restart_routines, analyze_routines

   restart_routines(events, "corner")
   analyze_routines(events, "corner", min_taker_attempts=3)
   # .detail / .summary / .team_profiles / .taker_profiles / .target_matrix

**Where it's used**
   :func:`~wa_setpieces.core.workflow.run_workflow`'s ``routines``/
   ``routine_summary``/``routine_team_profiles``/``routine_taker_profiles``/
   ``routine_target_matrix`` fields, for every type in :doc:`categories`.

Data-driven clusters
-------------------------

**What it describes**
   Deliveries grouped by geometric similarity (k-means over start/end
   x/y by default) instead of a fixed, hand-picked taxonomy -- surfaces
   whatever patterns a team actually repeats.

**Requirements**
   The ``ml`` extra (``pip install "wa-setpieces[ml]"``, scikit-learn).

**Compute it**

.. code-block:: python

   from wa_setpieces import cluster_routines, cluster_summary

   clustered = cluster_routines(events, "corner", n_clusters=5)
   # restart_routines' detail plus `cluster` (int, -1 = unclustered) and
   # an auto-generated `cluster_label` (e.g. "short, forward, central")
   cluster_summary(clustered)  # per-cluster usage/outcome roll-up

**Where it's used**
   :func:`~wa_setpieces.viz.plots.plot_routine_clusters` in the
   :ref:`gallery`; ``run_workflow``'s ``routine_clusters`` field.

Long throws
---------------

**What it describes**
   The one throw-in pattern that plays like a corner -- a direct ball
   into a crowded box, where a genuine long-throw specialist is a real
   tactical weapon. Per-player usage/threat, and flick-on/knockdown
   detection restricted to throws past a distance threshold.

**Requirements**
   ``throw_in`` only.

**Compute it**

.. code-block:: python

   from wa_setpieces import long_throw_taker_summary, long_throw_second_phases

   long_throw_taker_summary(events, min_distance=25.0)
   # per-player usage share and threat created (shots/goals via the
   # assist-chain link) among throw-ins that travel at least min_distance

   long_throw_second_phases(events, min_distance=25.0)
   # event-sequence-based flick-on/knockdown detection, restricted to
   # those same long throws

**Where it's used**
   The throw-in section of :doc:`categories` -- the closest thing
   throw-ins have to a value model, since there's no xT path for this
   type (see :doc:`value_models`).

Penalty placement
----------------------

**What it describes**
   *Where in the goal* each penalty was placed -- ``goal_y_norm``/
   ``goal_h_norm`` (0-1 across/up the frame), ``corner_zone`` (a 3x3
   grid), ``placement_score`` (distance from center) -- plus per-taker
   conversion rate.

**Requirements**
   ``penalty`` only -- penalties are shots, not passes, detected on shot
   events rather than the pass-based machinery everything else here
   uses. Pure geometry, no optional dependency needed.

**Compute it**

.. code-block:: python

   from wa_setpieces import penalty_placement_detail, penalty_taker_summary

   penalty_placement_detail(events)
   penalty_taker_summary(events)

**Where it's used**
   The penalty section of :doc:`categories`; shares its goal-mouth
   geometry with :mod:`wa_setpieces.ml.shot_value` (:doc:`value_models`).
