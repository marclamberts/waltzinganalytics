opta-setpieces
===============

Set-piece metrics for football (soccer) matches from **Opta / Stats Perform
F24** event-feed JSON exports: penalties, kick-offs, free kicks, corners,
throw-ins and goal kicks.

Given a raw F24 match file, this package tags every set-piece restart,
aggregates attempts and success rates by team and player, tracks pass end
locations for delivery maps, and links each set piece to the shot or goal
it produced.

.. code-block:: python

   from opta_setpieces import load_events, set_piece_summary

   match = load_events("match.json")
   print(set_piece_summary(match.events))

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   quickstart
   qualifiers
   api
   changelog
