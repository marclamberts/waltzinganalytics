Expected threat, added value and ratings
===========================================

Three layers, each built on the last: a grid of pitch-zone values (xT),
a single value number per delivery that blends xT with shot quality
(added value), and a benchmarked 0-100 score per team or player
(rating). All three are only meaningful for **corner and free kick** --
the two phase-based, shot-threat set pieces -- see :doc:`../categories`'
coverage matrix for what the other four types get instead. Already know
which of these you want, and just need the how-to? :doc:`../value_models`
covers the same ground organized model-by-model instead of narratively,
plus the two ratings this page doesn't (defensive rating, and the
experimental ML-based shot value).

Expected Threat (xT)
------------------------

:class:`~wa_setpieces.XTModel` implements Karun Singh's grid-based xT
method: fit a grid of zone values from data, then value any pass as
``xT[end_zone] - xT[start_zone]``.

.. important::

   Fit on as many matches as you can. A single match is nowhere near
   enough data for a trustworthy grid -- treat single-match results as a
   demonstration of the mechanism, not real analysis.

.. code-block:: python

   from wa_setpieces import XTModel, load_events_multi, set_piece_delivery_xt, set_piece_xt_summary

   # Fit once across as many matches as you have, then reuse:
   season_events = load_events_multi(match_files)  # see loading a season, in the user guide
   model = XTModel.fit(season_events)

   set_piece_delivery_xt(match.events, "corner", model)    # per-delivery xt_start/xt_end/xt_added
   set_piece_xt_summary(match.events, "free_kick", model)  # per-team total/average xT added

   model.to_csv("xt_grid.csv")               # persist a grid you trust
   model2 = XTModel.from_csv("xt_grid.csv")  # reload it for later matches, no refit needed

``xt_added`` is ``NaN`` for unsuccessful deliveries -- there's no reliable
end location for a pass that didn't find a teammate, so no threat value
can be attributed to where it *would* have gone.

Added value
--------------

:mod:`wa_setpieces.core.value` blends two things into one number per
delivery: the xT added by the delivery itself, and -- if it produced a
shot, whether straight off the ball or via a second-phase loose ball --
how good a chance that shot was (``model.shot_value``, the scoring
probability of the zone the shot came from).
``added_value = delivery_xt_added + shot_value``, always a real number
(0 where nothing happened), so it's always summable across a whole match
or season.

.. code-block:: python

   from wa_setpieces import set_piece_added_value, set_piece_value_summary, XTModel

   model = XTModel.fit(match.events)
   set_piece_added_value(match.events, "corner", model)    # per-delivery breakdown
   set_piece_value_summary(match.events, "corner", model)  # per-team total/average

:func:`~wa_setpieces.corner_report` and :func:`~wa_setpieces.free_kick_report`
(``set_piece_report`` generalized to any type) merge attempts, success
rate, second-phase rate, retention rate, and -- with a model -- added
value and goals into one table per team:

.. code-block:: python

   from wa_setpieces import corner_report

   corner_report(match.events, model=model)

.. important::

   The shot a delivery "produced" is resolved via Opta's own assist-chain
   qualifier, not a positional guess -- see :doc:`metrics`'s "Linking to
   shots and goals" for why an unscoped ``eventId`` lookup would silently
   corrupt this.

Ratings
----------

:mod:`wa_setpieces.core.rating` turns a report into a single 0-100 "how
good" score, benchmarked against whoever else is in the table -- there is
no universal 50. Always rate a full season/competition, not one match; a
two-row single-match sample only tells you which of those two teams had
the better match, not how good either one actually is.

Each component metric is z-scored against the sample
(``50 + z * 15``, clipped to ``[0, 100]`` -- roughly SAT-style: 50 is the
sample mean, +/-1 SD is +/-15 points), then combined by a weighted mean.
Team ratings build on ``set_piece_report``'s own columns (``success_rate``,
``avg_added_value``, ``retention_rate``). Player ratings split into two
independently benchmarked halves -- a **delivery score** (taker quality)
and a **finishing score** (shooter quality) -- so a player who's good at
one and never does the other is rated on the component they actually
have, not penalized for the one they don't.

.. code-block:: python

   from wa_setpieces import team_rating, player_rating

   team_rating(corner_report(season_events, model=model))
   player_rating(season_events, "corner", model, min_deliveries=5, min_shots=3)
