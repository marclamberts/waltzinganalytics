.. _by-value-model:

By value model
================

"Value model" isn't one thing in this package -- it's a small chain of
them, each building on the last. This page is the same kind of reference
as :doc:`categories`, just organized by *value model* instead of *set
piece*: pick one below, see what it measures, what it needs, and how to
compute it.

How they connect
--------------------

.. code-block:: text

   XTModel.value            -- "how dangerous is this pitch zone"
        |
        +-- XTModel.action_value    -- xT added by one delivery
        |
        +-- XTModel.shot_value      -- P(goal) if a shot is taken from here
                 |
                 v
   set_piece_added_value  =  delivery's xT added  +  shot_value of the shot it produced
        |
        v
   team_rating / player_rating  -- both benchmarked 0-100 against a sample

``wa_setpieces.ml.shot_value`` is a separate, independent shot-scorer --
a bundle of five pre-trained gradient-boosted models, richer than
``XTModel.shot_value`` but not (yet) wired into ``added_value`` or the
ratings above it. See its own section below for why the two aren't the
same thing.

Expected Threat (xT)
-------------------------

**What it measures**
   How dangerous a pitch zone is: the probability that possession
   starting there eventually leads to a goal, expressed 0-1 per zone on
   a grid. Karun Singh's grid-based method -- fit once from data, then
   value any pass as ``xT[end_zone] - xT[start_zone]``.

**Requirements**
   As many matches as you can fit on -- a single match is nowhere near
   enough data for a trustworthy grid (see :doc:`user_guide/value_and_ratings`).
   No optional extras needed; pure ``pandas``/``numpy``.

**Compute it**

.. code-block:: python

   from wa_setpieces import XTModel, load_events_multi

   season_events = load_events_multi(match_files)
   model = XTModel.fit(season_events)

   model.value(x=95, y=40)                       # xT of one pitch location
   model.action_value(80, 30, 95, 40)             # xT added by one pass
   model.shot_value(95, 40)                       # P(goal) if shot from here -- fit() only

   model.save("xt_grid.npz")                      # full model, including shot/goal grids
   model2 = XTModel.load("xt_grid.npz")            # reload later, no refit needed

**Where it's used**
   Everything below this section. Only ``corner`` and ``free_kick`` have
   a wired-in xT path today -- see :doc:`categories`'s coverage matrix.

Added value
--------------

**What it measures**
   One number per set-piece delivery, blending the delivery's own xT
   added with -- if it produced a shot -- how good that chance was:
   ``added_value = delivery_xt_added + shot_value``. Always a real
   number (0 where nothing happened), so it's summable across a match
   or season.

**Requirements**
   A fitted :class:`~wa_setpieces.XTModel` (from :meth:`XTModel.fit`, not
   :meth:`XTModel.from_csv` -- the shot-value grids aren't persisted by
   ``to_csv``/``from_csv``, only by ``save``/``load``). Only meaningful
   for ``"corner"``/``"free_kick"`` -- see :func:`~wa_setpieces.core.value.set_piece_added_value`'s
   own docstring.

**Compute it**

.. code-block:: python

   from wa_setpieces import set_piece_added_value, set_piece_value_summary

   set_piece_added_value(match.events, "corner", model)    # per-delivery breakdown
   set_piece_value_summary(match.events, "corner", model)  # per-team total/average

The shot a delivery "produced" is resolved via Opta's own assist-chain
qualifier (:func:`~wa_setpieces.link_set_piece_shots`), not a positional
guess -- see :doc:`user_guide/metrics`'s "Linking to shots and goals".

**Where it's used**
   Feeds directly into ``team_rating``'s ``avg_added_value`` component and
   ``player_rating``'s delivery-score half, for corner/free kick.

Shot value (experimental, ML-based)
----------------------------------------

**What it measures**
   A richer, five-model shot quality score --
   :mod:`wa_setpieces.ml.shot_value` -- distinct from ``XTModel.shot_value``
   above. Five gradient-boosted models (P(on target), xG-on-target,
   post-shot xG, a situational signal, a 4-class outcome distribution),
   blended into one ``shot_value`` column per shot.

.. important::

   This is **not** what ``set_piece_added_value`` uses -- that's the
   grid-based ``XTModel.shot_value``, fit from your own data, dependency-free.
   This module is pre-trained, heavier, and richer, but several of its
   input features are reconstructed best-effort guesses from Opta
   qualifiers rather than confirmed ground truth. **Read the module
   docstring in full before trusting the output** -- it documents exactly
   which columns are confidently derived versus experimental.

**Requirements**
   The ``ml`` extra: ``pip install "wa-setpieces[ml]"`` (xgboost,
   scikit-learn, joblib). Models ship inside the package (~4.5MB), no
   external download or training required.

**Compute it**

.. code-block:: python

   from wa_setpieces.ml.shot_value import shot_value, ShotValueModels

   models = ShotValueModels.load()     # load once, reuse across matches
   shot_value(match.events, models)    # one row per shot: on_target_prob, xgot, psxg, shot_value

**Where it's used**
   Standalone today -- not wired into ``added_value`` or the ratings
   below. Use it when you want a second, independent shot-quality opinion
   to compare against the xT-grid-based one, not as a drop-in replacement.

Team rating
--------------

**What it measures**
   A single 0-100 "how good" score per team, benchmarked against
   whoever else is in the table (z-scored, ``50 + z * 15``, clipped to
   ``[0, 100]``). There is no universal 50 -- always rate a full
   season/competition, not one match.

**Requirements**
   A :func:`~wa_setpieces.core.report.set_piece_report` table. Works
   with or without a fitted model -- without one, the rating drops the
   added-value component and scores off success rate and retention rate
   alone (this is how throw-in/penalty/goal-kick/kick-off get a rating
   despite having no xT path -- see :doc:`categories`).

**Compute it**

.. code-block:: python

   from wa_setpieces import team_rating, corner_report

   team_rating(corner_report(season_events, model=model))       # with added value
   team_rating(corner_report(season_events))                    # without -- success/retention only

**Where it's used**
   Every set-piece type gets one -- the one rating in this package with
   no coverage gaps.

Player rating
----------------

**What it measures**
   Two independently benchmarked halves: a **delivery score** (taker
   quality, from ``added_value`` grouped by who took the set piece) and a
   **finishing score** (shooter quality, from ``XTModel.shot_value`` on
   every shot traced back to this set-piece type, grouped by who took
   the shot). Merged so a pure taker or pure finisher is rated on the
   component they actually have.

**Requirements**
   A fitted :class:`~wa_setpieces.XTModel`. Only meaningful for
   ``"corner"``/``"free_kick"`` -- same coverage as added value, since
   it's built from it.

**Compute it**

.. code-block:: python

   from wa_setpieces import player_rating

   player_rating(season_events, "corner", model, min_deliveries=5, min_shots=3)
   # columns: delivery_score / finishing_score / rating, per player

``min_deliveries``/``min_shots`` exclude too-small samples from being
rated on noise rather than skill -- see :mod:`wa_setpieces.core.rating`'s
module docstring.

**Where it's used**
   Corner/free-kick player breakdowns only -- ``None`` for every other
   type in :func:`~wa_setpieces.run_workflow`'s output.

Defensive rating
--------------------

**What it measures**
   The conceding-side mirror of team rating -- 0-100, but *lower*
   concessions score *better* (the metrics are negated before z-scoring,
   so "100" always means "best defensively," same direction as attacking
   ratings).

**Requirements**
   A :func:`~wa_setpieces.core.defending.defensive_set_piece_summary`
   table (needs ``opponent_success_rate``, ``shots_conceded_per_100``,
   ``goals_conceded``).

**Compute it**

.. code-block:: python

   from wa_setpieces import defensive_set_piece_summary, defensive_rating

   defensive_rating(defensive_set_piece_summary(match.events))

**Where it's used**
   Standalone -- the opponent-scouting side of :doc:`user_guide/defending_and_season`,
   not blended into the attacking ``team_rating`` above.
