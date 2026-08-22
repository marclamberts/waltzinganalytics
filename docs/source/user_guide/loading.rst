Loading and extracting data
=============================

Everything else in this guide starts from one events
:class:`pandas.DataFrame` -- one row per event, one column per Opta
qualifierId (named ``q_<id>``). This page covers how that frame gets
built, from one match or many, from Opta or StatsBomb, and how to pull
just the set pieces back out of it.

Load one match
----------------

:func:`~wa_setpieces.load_events` reads an F24 JSON file (or an
already-parsed ``dict``) and returns a
:class:`~wa_setpieces.core.loader.Match`: the raw ``matchDetails`` block,
plus the tidy events frame.

.. code-block:: python

   from wa_setpieces import load_events

   match = load_events("match.json")
   match.events.head()

Other data providers
------------------------

Opta F24 is the native format, handled directly above. StatsBomb
open-data exports go through an adapter first --
:func:`~wa_setpieces.load_statsbomb_events` converts them into the same
internal events frame, so every function in this guide works unchanged
on either source:

.. code-block:: python

   from wa_setpieces import load_statsbomb_events

   events = load_statsbomb_events("statsbomb_events_export.json")

See :mod:`wa_setpieces.providers.statsbomb`'s module docstring for
exactly what is (and isn't) faithfully mapped -- a few Opta-only fields
(some routine/technique detail in particular) don't have a StatsBomb
equivalent and come back ``None`` rather than a guess.

Extract just the set pieces
-------------------------------

Each set-piece type has a dedicated extractor that filters the events
frame down to just that restart:

.. code-block:: python

   from wa_setpieces import (
       extract_corners, extract_free_kicks, extract_throw_ins,
       extract_goal_kicks, extract_kick_offs, extract_penalties,
       extract_all,
   )

   corners = extract_corners(match.events)
   all_set_pieces = extract_all(match.events)  # dict: name -> DataFrame

To label every event in place instead -- keeping open-play events in the
frame, just tagged -- use :func:`~wa_setpieces.tag_set_pieces`, which adds
a ``set_piece_type`` column (``None`` for anything that isn't one):

.. code-block:: python

   from wa_setpieces import tag_set_pieces

   tagged = tag_set_pieces(match.events)
   tagged[tagged["set_piece_type"] == "corner"]

Every extractor and qualifier this relies on is documented in the
:doc:`../qualifiers` reference, including the two places (in-swinger vs.
footedness, and an ``eventId`` collision across teams) where getting this
wrong is an easy, quiet mistake.

Loading several matches
--------------------------

:func:`~wa_setpieces.load_events_multi` loads and stacks several F24
exports into one events frame, tagged with a ``matchId`` column -- F24
carries no match identifier of its own, and per-match ``eventId``
numbering restarts at 1, so without this, rows from different matches
would collide.

.. code-block:: python

   from wa_setpieces import load_events_multi, team_set_piece_counts

   season = load_events_multi(["2026-02-20_match.json", "2026-02-27_match.json"])
   team_set_piece_counts(season)   # aggregated across every match passed in

.. important::

   This is for **match-independent aggregation only** -- team/player
   counts, zone heatmaps, and :meth:`~wa_setpieces.XTModel.fit` all work
   fine on the combined frame, since those operate row-by-row or via
   groupby. The temporal-window functions in :mod:`wa_setpieces.core.phases`
   and :mod:`wa_setpieces.core.retention` assume one chronologically-ordered
   match -- :func:`~wa_setpieces.core.phases.classify_phase` requires
   exactly two contestants in its input, and
   :func:`~wa_setpieces.retention_detail` explicitly rejects a frame with
   more than one ``matchId`` -- both raise loudly rather than letting a
   window silently bleed across a match boundary. Run those per match and
   concatenate the *results*:

   .. code-block:: python

      import pandas as pd
      from wa_setpieces import load_events
      from wa_setpieces.core.phases import second_phases

      all_second_phases = pd.concat(
          [second_phases(load_events(f).events, "corner") for f in match_files]
      )

For real season work -- rolling form, whole-season roll-ups, safe
match-boundary handling done for you -- reach for
:class:`~wa_setpieces.SeasonDataset` instead of calling
``load_events_multi`` directly; see :doc:`defending_and_season`.
