Visualisation
================

Pitch plots for everything covered in this guide, built on
`mplsoccer <https://mplsoccer.readthedocs.io>`_. This page is the tour of
what exists and how the shared styling works; the :doc:`../gallery/index`
has every plot below rendered in full, in both light and dark mode, with
the exact source that made it.

.. code-block:: bash

   pip install -e ".[viz]"   # matplotlib + mplsoccer

.. code-block:: python

   from wa_setpieces.viz.plots import (
       plot_delivery_map,      # arrow map of deliveries, colored by outcome
       plot_zone_heatmap,      # where events happen, gridded onto the pitch
       plot_xt_grid,           # a fitted XTModel's grid, as a heatmap
       plot_second_phase,      # one corner/free-kick's phase sequence, numbered
       plot_team_comparison,   # grouped bars: both teams, every set-piece type
       plot_xt_added_bars,     # diverging bar chart of xT added per delivery
       plot_corner_sonar,      # polar plot of delivery angle + distance
       plot_match_timeline,    # every set piece on one shared match-minute axis
       plot_dashboard,         # one-figure report card combining several of the above
       plot_set_piece_radar,   # two-team radar over a corner_report/free_kick_report
       plot_set_piece_outcomes,      # shot map: every delivery, colored by outcome
       plot_rating_benchmark,        # team/player rating vs. the sample-average baseline
       plot_routine_clusters,        # delivery map colored by cluster_routines' clusters
       plot_defensive_routine_bars,  # what a team concedes most, by routine or zone
       plot_aerial_duel_win_rate,    # per-team aerial-duel win rate
   )

   plot_delivery_map(
       delivery_locations(match.events, "corner"), title="Corner deliveries",
       subtitle="20 June 2026 - Delivery map", footer="Data: Opta", dark=False,  # or dark=True (default)
   )
   plot_dashboard(match.events, team_id, set_piece_type="corner")  # the "hero" figure

.. image:: /gallery/images/sphx_glr_plot_10_dashboard_001.png
   :alt: One-figure set-piece dashboard combining several plot types
   :align: center
   :width: 640px

One figure, both themes
---------------------------

Every plotting function returns ``(fig, ax)`` (``plot_dashboard`` returns
just ``fig``, being multi-panel) for further customization, and takes
``dark: bool = True`` -- the whole figure switches between a validated
dark (navy) and light (white) palette with that one argument. See the
:ref:`gallery`'s light/dark example for the same chart in both modes side
by side.

Colors are assigned by the job they do, not picked for looks --
:mod:`wa_setpieces.viz.theme` is the reference:

- a validated categorical palette for team identity (team-vs-team charts
  use a fixed orange-then-blue pairing in both modes)
- a status pair for success/fail
- gold for goals
- single-hue sequential ramps for magnitude
- a diverging pair for signed quantities, like xT added

``subtitle`` (a muted line under the title) and ``footer`` (a small
credit/source line, bottom-right) are optional on every plot.

Video clips
--------------

:mod:`wa_setpieces.core.clips` isn't a plot, but belongs here: it turns a
delivery into an in/out timestamp window suitable for handing off to a
video-clipping tool, so "show me every long throw this half" becomes a
literal clip list instead of a scouting note.

See the :ref:`gallery` for all sixteen plots above, in both modes, with
full source code for each.
