Defending, opponent scouting and season form
===============================================

Everything so far reads a set piece from the attacking side. This page
flips that -- what does a team *concede* -- and then extends both
directions across a whole season, safely.

Defending
------------

:mod:`wa_setpieces.core.defending` flips the attacking-team metrics
covered elsewhere in this guide to "what does this team concede," per
match (requiring exactly two contestants, so the opponent can be
inferred unambiguously):

.. code-block:: python

   from wa_setpieces import (
       defensive_set_piece_summary, defensive_rating,
       defensive_routine_summary, defensive_zone_summary,
   )

   defensive_set_piece_summary(match.events)  # attempts/shots/goals conceded, per team
   defensive_rating(defensive_set_piece_summary(match.events))  # 0-100, lower concessions score better

   defensive_routine_summary(match.events, "corner")  # conceded, by routine type
   defensive_zone_summary(match.events, "corner")     # conceded, by destination zone

Opponent scouting reports
-----------------------------

:func:`~wa_setpieces.opponent_scouting_report_html` turns the last two
(plus aerial-duel record) into a ready-to-view pre-match scouting report
on one opponent -- the conceding-side mirror of
:func:`~wa_setpieces.corner_report_html`:

.. code-block:: python

   from pathlib import Path
   from wa_setpieces import opponent_scouting_report_html

   html = opponent_scouting_report_html(
       match.events, opponent_id="...", set_piece_type="corner", team_name="Rivals FC",
   )
   Path("scouting.html").write_text(html, encoding="utf-8")

Or from the command line:

.. code-block:: bash

   wa-setpieces scout match.json --opponent <contestantId> --type corner --output scouting.html

Season form with SeasonDataset
----------------------------------

:doc:`loading` covers ``load_events_multi`` for simple match-independent
aggregation. :class:`~wa_setpieces.SeasonDataset` builds on that same
pattern -- validates the ``matchId`` boundary up front, and does the
per-match-then-concatenate dance for you -- and adds rolling attacking
*and* defensive form on top:

.. code-block:: python

   from wa_setpieces import SeasonDataset

   season = SeasonDataset.from_sources(match_files)  # chronological order matters, see below
   season.summary()                            # competition totals and per-match rates
   season.report("corner", model)              # match-level report rows -- one per (team, match)
   season.season_report("corner", model)       # the same fields, rolled up into one row per team
   season.rolling_summary(window=5)            # rolling attacking form
   season.rolling_defensive_summary(window=5)  # rolling defensive form (conceding side)

:meth:`~wa_setpieces.core.season.SeasonDataset.season_report` sums every
underlying count across matches first and re-derives rates from those
sums -- the same idiom ``rolling_summary``/``rolling_defensive_summary``
use for a trailing window, applied to the whole season instead. It never
averages a per-match rate directly: a match with 8 corners and a match
with 1 should not count equally toward a season conversion rate.

.. important::

   ``rolling_summary``/``rolling_defensive_summary`` are only meaningful
   if ``sources``/``match_ids`` were supplied to ``from_sources`` already
   in chronological order -- there's no date field in the loaded event
   schema to derive true match order from otherwise (a directory listing,
   for example, sorts alphabetically, not chronologically).

.. important::

   ``from_sources`` (and the underlying ``load_events_multi``) rejects two
   sources that resolve to the same ``matchId`` -- whether passed
   explicitly via ``match_ids`` or derived from the default file-stem
   convention (e.g. two different directories both containing a
   ``matchday3.json``) -- rather than silently merging two distinct
   matches into one. Every match-safety guarantee on this page depends on
   ``matchId`` actually being unique per match.

The command line runs this too:

.. code-block:: bash

   wa-setpieces season match_1.json match_2.json ... --action season-report --type corner --output season.csv

``--action`` is one of ``summary``, ``report``, ``season-report``,
``rolling`` or ``rolling-defense`` (``--window`` for the rolling ones);
see :doc:`reports_and_export` for the rest of the command-line interface.
