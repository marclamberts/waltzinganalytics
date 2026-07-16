Zones, second phases, retention and xT
=========================================

These four pieces build on the core extractors to answer questions the raw
qualifiers alone can't: *where* on the pitch did this happen, *did the
danger continue* after the initial contact, *did the team keep the ball*,
and *how much threat did the delivery create*.

Everything on this page is a **derived heuristic** layered on top of the F24
feed, not a field the provider gives you directly -- read each section's
caveats before relying on the numbers.

Zones, thirds and channels
-----------------------------

:mod:`opta_setpieces.zones` classifies pitch location using the confirmed
F24 convention that every event's ``x``/``y`` are in *that event's own
team's* attacking direction (``x=0`` own goal, ``x=100`` opponent's goal;
see :mod:`opta_setpieces.zones` module docstring for how this was verified
against the sample match).

.. code-block:: python

   from opta_setpieces import add_thirds, add_channels, add_zone_grid, zone_counts

   tagged = add_thirds(match.events)          # "defensive_third" / "middle_third" / "attacking_third"
   tagged = add_channels(tagged, n=5)          # wide / half-space / central (or n=3 for left/central/right)
   tagged = add_zone_grid(tagged)              # 6x3 = 18-zone grid label, e.g. "R1C4"

   zone_counts(match.events, group_cols=["contestantId"])  # heatmap-ready counts per zone per team

Apply these to :func:`~opta_setpieces.delivery_locations` output to see
which channel/third corners or free kicks are delivered *into*:

.. code-block:: python

   from opta_setpieces import delivery_locations
   from opta_setpieces.zones import add_channels

   corners = delivery_locations(match.events, "corner")
   corners_end = add_channels(corners, y_col="end_y", n=5)
   corners_end["channel"].value_counts()

Second phases
----------------

:mod:`opta_setpieces.phases` walks forward from every corner/free-kick
delivery and classifies what happened: did the defence clear it
immediately, was there a shot straight off the delivery, or did the ball
stay alive (a knockdown, blocked clearance, loose ball) long enough for the
attacking team to get a **second-phase shot** away.

.. code-block:: python

   from opta_setpieces import second_phases, second_phase_summary

   second_phases(match.events, "corner")        # one row per corner, with the classification
   second_phase_summary(match.events, "corner") # per-team roll-up: deliveries, second phases, goals

   second_phases(match.events, "free_kick")
   second_phase_summary(match.events, "free_kick")

There is no "phase" field in F24, so this is inferred from event sequencing
(time gaps, who touches the ball, whether a defensive clearance travels far
enough up the pitch). The thresholds are tunable:

.. code-block:: python

   from opta_setpieces.phases import second_phases

   second_phases(
       match.events, "corner",
       clear_safe_x=40,        # how far up the pitch a clearance must travel to count as "cleared"
       max_gap_seconds=6,      # a bigger gap between events ends the phase window
       max_total_seconds=15,   # hard cap on how long after the delivery we keep looking
   )

Retention
------------

:mod:`opta_setpieces.retention` asks a broader question than the raw pass
``outcome`` flag: did the team that took the set piece still have the ball
some seconds later (default 8s), regardless of whether the very first pass
found a teammate.

.. code-block:: python

   from opta_setpieces import retention_detail, retention_rate

   retention_detail(match.events, "corner")     # per-delivery: outcome vs. retained
   retention_rate(match.events, "throw_in")     # per-team retention rate
   retention_rate(match.events, "corner", window_seconds=5)

Works for ``kick_off``, ``free_kick``, ``corner``, ``throw_in`` and
``goal_kick``. Penalties are excluded (a penalty is a single shot, not a
restart with a meaningful "possession after" question).

Expected Threat (xT)
------------------------

:class:`opta_setpieces.XTModel` implements Karun Singh's grid-based xT
method: fit a grid of zone values from data, then value any pass as
``xT[end_zone] - xT[start_zone]``.

.. important::

   Fit on as many matches as you can. A single match (as in these examples)
   is nowhere near enough data for a trustworthy grid -- treat single-match
   results as a demonstration of the mechanism, not real analysis.

.. code-block:: python

   from opta_setpieces import XTModel, set_piece_delivery_xt, set_piece_xt_summary

   # Fit once across as many matches as you have, then reuse:
   # all_events = pd.concat([load_events(f).events for f in match_files])
   model = XTModel.fit(match.events)

   set_piece_delivery_xt(match.events, "corner", model)     # per-delivery xt_start/xt_end/xt_added
   set_piece_xt_summary(match.events, "free_kick", model)   # per-team total/average xT added

   model.to_csv("xt_grid.csv")            # persist a grid you trust
   model2 = XTModel.from_csv("xt_grid.csv")  # reload it for later matches, no refit needed

``xt_added`` is ``NaN`` for unsuccessful deliveries -- there's no reliable
end location for a pass that didn't find a teammate, so no threat value can
be attributed to where it *would* have gone.
