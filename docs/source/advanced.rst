Zones, second phases, retention, xT and added value
=======================================================

These pieces build on the core extractors to answer questions the raw
qualifiers alone can't: *where* on the pitch did this happen, *did the
danger continue* after the initial contact, *did the team keep the ball*,
*how much threat did the delivery create*, and -- combining several of
those -- *how much value did a set piece add, all in*.

Everything on this page is a **derived heuristic** layered on top of the F24
feed, not a field the provider gives you directly -- read each section's
caveats before relying on the numbers.

Zones, thirds and channels
-----------------------------

:mod:`wa_setpieces.core.zones` classifies pitch location using the confirmed
F24 convention that every event's ``x``/``y`` are in *that event's own
team's* attacking direction (``x=0`` own goal, ``x=100`` opponent's goal;
see :mod:`wa_setpieces.core.zones` module docstring for how this was verified
against the sample match).

.. code-block:: python

   from wa_setpieces import add_thirds, add_channels, add_zone_grid, zone_counts

   tagged = add_thirds(match.events)          # "defensive_third" / "middle_third" / "attacking_third"
   tagged = add_channels(tagged, n=5)          # wide / half-space / central (or n=3 for left/central/right)
   tagged = add_zone_grid(tagged)              # 6x3 = 18-zone grid label, e.g. "R1C4"

   zone_counts(match.events, group_cols=["contestantId"])  # heatmap-ready counts per zone per team

Apply these to :func:`~wa_setpieces.delivery_locations` output to see
which channel/third corners or free kicks are delivered *into*:

.. code-block:: python

   from wa_setpieces import delivery_locations
   from wa_setpieces.core.zones import add_channels

   corners = delivery_locations(match.events, "corner")
   corners_end = add_channels(corners, y_col="end_y", n=5)
   corners_end["channel"].value_counts()

Second phases
----------------

:mod:`wa_setpieces.core.phases` walks forward from every corner/free-kick
delivery and classifies what happened: did the defence clear it
immediately, was there a shot straight off the delivery, or did the ball
stay alive (a knockdown, blocked clearance, loose ball) long enough for the
attacking team to get a **second-phase shot** away.

.. code-block:: python

   from wa_setpieces import second_phases, second_phase_summary

   second_phases(match.events, "corner")        # one row per corner, with the classification
   second_phase_summary(match.events, "corner") # per-team roll-up: deliveries, second phases, goals

   second_phases(match.events, "free_kick")
   second_phase_summary(match.events, "free_kick")

There is no "phase" field in F24, so this is inferred from event sequencing
(time gaps, who touches the ball, whether a defensive clearance travels far
enough up the pitch). The thresholds are tunable:

.. code-block:: python

   from wa_setpieces.core.phases import second_phases

   second_phases(
       match.events, "corner",
       clear_safe_x=40,        # how far up the pitch a clearance must travel to count as "cleared"
       max_gap_seconds=6,      # a bigger gap between events ends the phase window
       max_total_seconds=15,   # hard cap on how long after the delivery we keep looking
   )

Retention
------------

:mod:`wa_setpieces.core.retention` asks a broader question than the raw pass
``outcome`` flag: did the team that took the set piece still have the ball
some seconds later (default 8s), regardless of whether the very first pass
found a teammate.

.. code-block:: python

   from wa_setpieces import retention_detail, retention_rate

   retention_detail(match.events, "corner")     # per-delivery: outcome vs. retained
   retention_rate(match.events, "throw_in")     # per-team retention rate
   retention_rate(match.events, "corner", window_seconds=5)

Works for ``kick_off``, ``free_kick``, ``corner``, ``throw_in`` and
``goal_kick``. Penalties are excluded (a penalty is a single shot, not a
restart with a meaningful "possession after" question).

Expected Threat (xT)
------------------------

:class:`wa_setpieces.XTModel` implements Karun Singh's grid-based xT
method: fit a grid of zone values from data, then value any pass as
``xT[end_zone] - xT[start_zone]``.

.. important::

   Fit on as many matches as you can. A single match (as in these examples)
   is nowhere near enough data for a trustworthy grid -- treat single-match
   results as a demonstration of the mechanism, not real analysis.

.. code-block:: python

   from wa_setpieces import XTModel, load_events_multi, set_piece_delivery_xt, set_piece_xt_summary

   # Fit once across as many matches as you have, then reuse:
   season_events = load_events_multi(match_files)  # see "Multiple matches" below
   model = XTModel.fit(season_events)

   set_piece_delivery_xt(match.events, "corner", model)     # per-delivery xt_start/xt_end/xt_added
   set_piece_xt_summary(match.events, "free_kick", model)   # per-team total/average xT added

   model.to_csv("xt_grid.csv")            # persist a grid you trust
   model2 = XTModel.from_csv("xt_grid.csv")  # reload it for later matches, no refit needed

``xt_added`` is ``NaN`` for unsuccessful deliveries -- there's no reliable
end location for a pass that didn't find a teammate, so no threat value can
be attributed to where it *would* have gone.

Multiple matches
-------------------

:func:`~wa_setpieces.load_events_multi` loads and stacks several F24
exports into one events DataFrame, tagged with a ``matchId`` column (F24
carries no match identifier of its own, and per-match ``eventId``
numbering restarts at 1, so without this rows from different matches would
collide).

.. code-block:: python

   from wa_setpieces import load_events_multi, team_set_piece_counts

   season = load_events_multi(["2026-02-20_match.json", "2026-02-27_match.json"])
   team_set_piece_counts(season)   # aggregated across every match passed in

.. important::

   This is for **match-independent aggregation only** -- team/player counts,
   zone heatmaps, and :meth:`XTModel.fit` all work fine on the combined
   frame, since those operate row-by-row or via groupby. The temporal-window
   functions in :mod:`wa_setpieces.core.phases` and :mod:`wa_setpieces.core.retention`
   assume one chronologically-ordered match; feeding them the combined frame
   directly would let a window bleed across a match boundary. Run those per
   match and concatenate the *results*:

   .. code-block:: python

      import pandas as pd
      from wa_setpieces import load_events
      from wa_setpieces.core.phases import second_phases

      all_second_phases = pd.concat(
          [second_phases(load_events(f).events, "corner") for f in match_files]
      )

Set-piece added value
-------------------------

:mod:`wa_setpieces.core.value` blends two things into one number per delivery:
the xT added by the delivery itself, and -- if it produced a shot, whether
straight off the ball or via a second-phase loose ball -- how good a
chance that shot was (``model.shot_value``, the scoring probability of
the zone the shot came from). ``added_value = delivery_xt_added +
shot_value``, always a real number (0 where nothing happened), so it's
always summable across a whole match or season.

.. code-block:: python

   from wa_setpieces import set_piece_added_value, set_piece_value_summary, XTModel

   model = XTModel.fit(match.events)
   set_piece_added_value(match.events, "corner", model)      # per-delivery breakdown
   set_piece_value_summary(match.events, "corner", model)    # per-team total/average

:func:`~wa_setpieces.corner_report` and :func:`~wa_setpieces.free_kick_report`
(``set_piece_report`` generalized to any type) merge attempts, success
rate, second-phase rate, retention rate, and -- with a model -- added
value and goals into one table per team:

.. code-block:: python

   from wa_setpieces import corner_report

   corner_report(match.events, model=model)

.. important::

   The shot a delivery "produced" is resolved via Opta's own assist-chain
   qualifier (:func:`~wa_setpieces.link_set_piece_shots`), not a
   positional guess. Getting this right required a real fix: **F24's
   ``eventId`` is only unique within one team's own event stream** -- both
   teams number their events 1, 2, 3, ... independently (confirmed against
   the sample match: 1464 of 1613 rows share an ``eventId`` with a
   same-numbered row from the *other* team). Every place in this package
   that resolves one delivery/shot by ``eventId`` scopes the lookup to a
   team (or narrows the search to just corner/free-kick deliveries and
   raises on remaining ambiguity, as :func:`~wa_setpieces.viz.plots.plot_second_phase`
   does) -- an unscoped ``events[events["eventId"] == x]`` lookup on the raw
   feed is not safe.
