"""Pitch and chart visualizations for set-piece data, built on `mplsoccer
<https://mplsoccer.readthedocs.io>`_ and matplotlib.

Every plotting function here takes the same DataFrames the rest of the
package produces (:func:`~wa_setpieces.delivery_locations`,
:func:`~wa_setpieces.core.zones.zone_counts`, an :class:`~wa_setpieces.XTModel`
grid, ...) and returns the ``(fig, ax)`` matplotlib pair, so you can keep
customizing the plot afterwards.

Requires the optional ``viz`` extra: ``pip install "wa-setpieces[viz]"``.
Opta coordinates (0-100 both axes, each event already in the acting
team's own attacking direction -- see :mod:`wa_setpieces.core.zones`) map
directly onto :class:`mplsoccer.Pitch`'s built-in ``pitch_type="opta"``, so
no coordinate conversion is needed.

Every function takes ``dark: bool = True`` -- the whole figure (pitch,
chart chrome, team colors) switches between the Waltzing Analytics dark
and light house-style palettes in :mod:`wa_setpieces.viz.theme` with that
one argument. Colors otherwise follow :mod:`wa_setpieces.viz.theme` --
assigned by the job they do (status, category, magnitude, sign, team
identity), not picked for looks. See that module's docstring before
adding a new plot.

Every function also takes ``eyebrow`` (a small category label above the
title, e.g. ``"Corner"``) and ``author`` (adds a personal byline under the
WA lockup, and an attribution/date stamp to the footer -- there's no
default author, so a chart from this package carries the WA brand mark
but not anyone's name unless you ask for it). Both are opt-in and blank
by default; see :meth:`wa_setpieces.viz.theme.Palette.draw_header`.

Every pitch-based function (a delivery map, a zone heatmap, ...) also
takes ``vertical: bool = False`` -- draws on :class:`mplsoccer.VerticalPitch`
instead of :class:`mplsoccer.Pitch` when ``True``, the same restart drawn
goal-at-top instead of goal-at-right. Both classes share the same drawing
API (arrows, scatter, heatmap, ...), so nothing else about a plotting
call changes -- mplsoccer itself already sizes the pitch correctly within
whichever figure canvas it's given; this module additionally picks a
taller default canvas for ``vertical=True`` so there's less unused
horizontal space than a landscape canvas would leave around a portrait
pitch.

Several functions also take ``show_stats: bool = True`` -- an
auto-computed headline stat strip (count, success rate, ...) under the
subtitle, so a chart states its own takeaway instead of leaving the
reader to work it out from the plot. These are computed from the data
actually being plotted, never passed in, so they can't drift out of
sync with what's drawn. :func:`plot_delivery_map` also takes
``density: bool = False`` -- a kernel-density shade of where deliveries
land underneath the arrows (:meth:`mplsoccer.Pitch.kdeplot`, via
seaborn, already a dependency of mplsoccer itself); off by default
since a smooth density surface overstates what a single match's handful
of deliveries can actually support -- turn it on for a season's worth.

Twenty-one functions answer questions the "plot the raw numbers"
functions above can't:

- :func:`plot_zone_scatter` -- every event as its own point (density-shaded
  by default), the individual-event alternative to :func:`plot_zone_heatmap`'s
  binned grid, for when the *shape* of a pattern matters more than exact
  per-zone counts.
- :func:`plot_set_piece_value_flow` -- cumulative added value per team
  over match time, a step chart showing *when* threat was created, not
  just the final total.
- :func:`plot_volume_quality_scatter` -- a labeled quadrant scatter,
  volume against quality, for when the question is whether doing
  something *often* also means doing it *well* -- a question no single
  bar chart metric answers on its own.
- :func:`plot_outcome_flow` -- a Sankey-style flow of every delivery from
  the restart, through its outcome category, down to whether it ended in
  a goal -- the only chart in this module built to show a *funnel*, not a
  ranking or a distribution.
- :func:`plot_rating_beeswarm` -- every player as one dot on a 0-100
  rating scale, spread just enough to avoid overlap, for when the
  question is how *spread out* a group's ratings are (one cluster, or a
  long tail) rather than each player's individual rank, which
  :func:`plot_rating_benchmark`'s bars already answer.
- :func:`plot_value_waterfall` -- one team's total set-piece added value,
  decomposed by restart type as a waterfall (floating bars stepping to a
  final total), for *which* type the value came from -- a different
  question than :func:`plot_set_piece_value_flow`'s *when*.
- :func:`plot_value_distribution` -- a violin plot of per-delivery added
  value, one per set-piece type, for the *spread* of outcomes a bar
  chart's average can't show.
- :func:`plot_type_radial_bar` -- a wind-rose bar chart of one metric
  across set-piece types, arranged around a circle instead of along an
  axis, so it reads as a team's restart *shape* rather than a ranking.
- :func:`plot_success_waffle` -- a single ratio (e.g. success rate) as a
  filled-square icon array, for when a headline number deserves more
  visual weight than a stat-strip figure.
- :func:`plot_type_outcome_mosaic` -- a Marimekko-style mosaic where
  segment *width* is volume (attempts) and segment *height* is quality
  (success rate), for when both need to be visible in the same chart
  rather than split across two.
- :func:`plot_team_parallel_coordinates` -- the same two-team profile
  comparison as :func:`plot_set_piece_radar`, on straight parallel axes
  instead of a circle, so every metric gets equal visual weight rather
  than however much a polar layout happens to exaggerate or compress it.
- :func:`plot_team_dumbbell` -- two teams' values per category as
  connected dot pairs, for when the *gap* between two series is the
  thing worth seeing directly rather than two bar lengths to compare by
  eye.
- :func:`plot_zone_bubble` -- zone counts as size-encoded bubbles on the
  pitch, a more intuitive (if less precise) encoding of "how many" than
  :func:`plot_zone_heatmap`'s color ramp.
- :func:`plot_kpi_bullet` -- a compact single-ratio bullet chart against
  qualitative bands and an optional target, built for a dashboard strip
  of several stacked together rather than one chart's worth of visual
  weight.
- :func:`plot_value_ridgeline` -- a joyplot of per-delivery added value,
  one smooth density curve per set-piece type, for a shape (multi-modal?
  skewed?) a violin's mirrored outline shows less clearly.
- :func:`plot_type_area_timeline` -- a stacked area chart of set-piece
  volume over match time, binned by type, for the *mix* shifting over
  the course of the match -- a different question than
  :func:`plot_match_timeline`'s individual dots (unaggregated) or
  :func:`plot_set_piece_value_flow`'s cumulative line (one signed
  value, not a volume breakdown).
- :func:`plot_success_ring` -- a single ratio as a circular progress
  ring, a different visual metaphor for the same job
  :func:`plot_success_waffle` does with filled squares.
- :func:`plot_half_comparison_slope` -- each set-piece type's value in
  the first half versus the second, as a two-point connected line, so
  the *direction of change* is a slope your eye reads directly rather
  than two numbers to compare mentally.
- :func:`plot_delivery_combination_network` -- a node-link graph of
  which player takes deliveries and which teammate usually wins the
  first contact -- the only chart here for an open set of players
  connected by who-delivers-to-whom, rather than a fixed small set of
  teams or categories.
- :func:`plot_metric_histogram` -- a classic binned histogram of any
  continuous metric, with no smoothing assumption baked in the way
  :func:`plot_value_distribution`'s violins and
  :func:`plot_value_ridgeline`'s KDE curves both have.
- :func:`plot_value_boxplot` -- exact quartiles, median and outliers
  per set-piece type, for when the specific numbers matter more than
  the overall distribution shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from mplsoccer import Pitch, VerticalPitch
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "wa_setpieces.viz requires the 'viz' extra: pip install \"wa-setpieces[viz]\""
    ) from exc

from . import theme

# Backwards-compatible aliases (pre-theme-module names, dark palette).
PITCH_COLOR = theme.SURFACE
LINE_COLOR = theme.PITCH_LINE
SUCCESS_COLOR = theme.GOOD
FAIL_COLOR = theme.CRITICAL


def _new_pitch(pal: theme.Palette, pitch_type: str = "opta", vertical: bool = False, **pitch_kwargs) -> Pitch:
    kwargs = dict(pitch_color=pal.surface, line_color=pal.pitch_line, linewidth=1.5)
    kwargs.update(pitch_kwargs)
    pitch_cls = VerticalPitch if vertical else Pitch
    return pitch_cls(pitch_type=pitch_type, **kwargs)


def _draw_pitch(pal: theme.Palette, ax, pitch_kwargs, vertical: bool = False, figsize=None):
    pitch = _new_pitch(pal, vertical=vertical, **(pitch_kwargs or {}))
    if figsize is None:
        figsize = (5.6, 8.2) if vertical else (8, 5.2)
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=figsize)
    else:
        pitch.draw(ax=ax)
    return pitch, fig, ax


def _style_chart_axis(pal: theme.Palette, ax) -> None:
    """Chart chrome only (facecolor, spines, ticks) -- title/subtitle are
    handled by :func:`_finish_figure` instead, since whether they belong on
    the axes or in a figure-level header band depends on whether this
    function owns the whole figure (see that function's docstring)."""
    ax.set_facecolor(pal.surface)
    for spine in ax.spines.values():
        spine.set_color(pal.gridline)
    ax.tick_params(colors=pal.ink_secondary)
    ax.xaxis.label.set_color(pal.ink_secondary)
    ax.yaxis.label.set_color(pal.ink_secondary)


def _reserve_ytick_margin(fig, ax, min_in: float = 0.35, pad_in: float = 0.18) -> None:
    """Reserve enough left margin for ``ax``'s y-tick labels, measured (not
    guessed) from their actual rendered width -- a bar chart's default left
    margin is a fixed fraction of the figure, which clips long labels (a
    truncated ``contestantId`` like ``"…gwrezdts7c"`` losing its first
    character) rather than growing to fit them. Skipped when there are no
    visible y-tick labels to measure."""
    labels = [t for t in ax.get_yticklabels() if t.get_text()]
    if not labels:
        return
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    widest_px = max(t.get_window_extent(renderer=renderer).width for t in labels)
    fig_w_in, _ = fig.get_size_inches()
    needed_in = max(widest_px / fig.dpi + pad_in, min_in)
    fig.subplots_adjust(left=min(0.5, needed_in / fig_w_in))


def _beeswarm_offsets(values: np.ndarray, bin_width: float, spacing: float = 0.22) -> np.ndarray:
    """Deterministic vertical offsets for a 1-D beeswarm: bucket ``values``
    into ``bin_width``-wide bins, then stack each bin's points alternating
    above/below the center line (0, +1, -1, +2, -2, ...) so points with a
    close value spread apart just enough not to overlap, instead of a
    random jitter that can still collide or a physics packing that's
    overkill for a handful of points."""
    order = np.argsort(values, kind="stable")
    counts: dict[int, int] = {}
    offsets = np.zeros(len(values))
    for idx in order:
        b = round(float(values[idx]) / bin_width)
        n = counts.get(b, 0)
        if n > 0:
            k = (n + 1) // 2
            sign = 1 if n % 2 == 1 else -1
            offsets[idx] = sign * k * spacing
        counts[b] = n + 1
    return offsets


def _declutter_points(xs: list[float], ys: list[float], min_dist: float = 3.2) -> tuple[list[float], list[float]]:
    """Nudge points that land within ``min_dist`` of an already-placed
    point onto a small circle around their own true position, in the
    order given -- so a cluster of near-coincident events (a goalmouth
    scramble, several touches in the same square meter) spreads into a
    readable rosette instead of stacking into one unreadable blob.
    Points far from anything already placed are left exactly where they
    are."""
    out_x: list[float] = []
    out_y: list[float] = []
    for x, y in zip(xs, ys):
        nearby = sum(1 for px, py in zip(out_x, out_y) if abs(px - x) < min_dist and abs(py - y) < min_dist)
        if nearby:
            angle = nearby * (2 * np.pi / 6)
            out_x.append(x + min_dist * 0.65 * np.cos(angle))
            out_y.append(y + min_dist * 0.65 * np.sin(angle))
        else:
            out_x.append(x)
            out_y.append(y)
    return out_x, out_y


def _flow_ribbon(ax, x0: float, x1: float, ya0: float, ya1: float, yb0: float, yb1: float, color: str, alpha: float = 0.55, zorder: int = 2) -> None:
    """Draw one Sankey-style ribbon: a smooth band connecting segment
    ``[ya0, ya1]`` on the left node (at ``x0``) to segment ``[yb0, yb1]``
    on the right node (at ``x1``), via a cubic Bezier on the top and
    bottom edges with the control points at the horizontal midpoint --
    the standard construction for a proportional flow diagram."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    xm = (x0 + x1) / 2
    verts = [
        (x0, ya1), (xm, ya1), (xm, yb1), (x1, yb1),
        (x1, yb0), (xm, yb0), (xm, ya0), (x0, ya0),
        (x0, ya1),
    ]
    codes = [
        Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
        Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=zorder))


def _finish_figure(
    pal: theme.Palette, fig, ax,
    title: str | None, subtitle: str | None, footer: str | None,
    eyebrow: str | None = None, author: str | None = None,
    stats: list[tuple[str, str]] | None = None,
) -> None:
    """Wrap up a plot: the full WA card header/footer (eyebrow, serif
    title, subtitle, headline stat strip, WA lockup, footer) if this
    function created and owns the whole figure -- or the older, simpler
    axes-level title/footer if the caller passed in their own ``ax``,
    since then we don't know the rest of that figure's layout and can't
    safely reserve margin for a header band without possibly colliding
    with whatever else is on it. ``stats`` (a chart's own auto-computed
    headline numbers) is silently dropped in that fallback case for the
    same reason.
    """
    if fig is not None:
        fig.patch.set_facecolor(pal.surface)
        fig.set_layout_engine(None)  # see Palette.draw_header's docstring
        _reserve_ytick_margin(fig, ax)
        pal.draw_header(fig, eyebrow=eyebrow, title=title, subtitle=subtitle, author=author, stats=stats)
        pal.draw_footer(fig, source=footer, author=author)
    else:
        pal.style_axis_text(ax, title, subtitle)
        if footer:
            pal.style_footer(ax.figure, footer)


def plot_delivery_map(
    deliveries: pd.DataFrame,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    density: bool = False,
    show_stats: bool = True,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Arrow map of set-piece deliveries, from :func:`~wa_setpieces.delivery_locations`.

    Successful deliveries (``outcome == 1``) are drawn in the status "good"
    color, unsuccessful ones in "critical" -- outcome is a status, not a
    team identity, so it never borrows the categorical team palette.

    Args:
        dark: render on the dark (default) or light palette from
            :mod:`wa_setpieces.viz.theme`.
        vertical: draw on a vertical (goal-at-top) pitch via
            :class:`mplsoccer.VerticalPitch` instead of the default
            horizontal (goal-at-right) :class:`mplsoccer.Pitch`.
        density: shade a kernel-density estimate of where deliveries land
            underneath the arrows (:meth:`mplsoccer.Pitch.kdeplot`, which
            needs ``seaborn`` -- already pulled in by mplsoccer itself).
            Off by default: a KDE surface implies a smooth, continuous
            pattern that a handful of deliveries from one match can't
            actually support -- turn this on for a season's worth of
            deliveries, where the shape means something.
        show_stats: show an auto-computed headline stat strip (delivery
            count and success rate) under the subtitle -- the chart
            states its own takeaway instead of leaving the reader to
            count arrows and colors by eye. Computed from ``deliveries``
            itself, not passed in.
        subtitle: optional muted line under the title (e.g. a date/venue).
        eyebrow: optional small category label above the title (e.g.
            ``"Corner"``), WA-house-style.
        footer: optional small credit/source line, bottom-left of the
            figure -- never defaulted.
        author: optional byline -- adds a name under the WA lockup and a
            "{author} | Created on DD-MM-YYYY" stamp to the footer.

    Returns:
        ``(fig, ax)``. ``fig`` is ``None`` if an existing ``ax`` was passed in.
    """
    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    success = deliveries[deliveries["outcome"] == 1]
    fail = deliveries[deliveries["outcome"] != 1]

    if density and len(deliveries.dropna(subset=["end_x", "end_y"])) >= 5:
        valid_ends = deliveries.dropna(subset=["end_x", "end_y"])
        pitch.kdeplot(
            valid_ends["end_x"], valid_ends["end_y"], ax=ax, cmap=pal.sequential_blue_cmap(),
            fill=True, levels=8, thresh=0.05, alpha=0.55, zorder=1,
        )

    if not fail.empty:
        pitch.arrows(
            fail["x"], fail["y"], fail["end_x"], fail["end_y"],
            ax=ax, color=pal.critical, width=2.4, headwidth=6.5, headlength=6.5,
            alpha=0.85, zorder=2, label="Unsuccessful",
        )
    if not success.empty:
        pitch.arrows(
            success["x"], success["y"], success["end_x"], success["end_y"],
            ax=ax, color=pal.good, width=2.8, headwidth=7, headlength=7,
            alpha=0.95, zorder=3, label="Successful",
        )

    pal.style_legend(ax)
    stats = None
    if show_stats and len(deliveries):
        success_rate = len(success) / len(deliveries)
        stats = [(str(len(deliveries)), "deliveries"), (f"{success_rate * 100:.0f}%", "success rate")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=stats)
    return fig, ax


def plot_zone_heatmap(
    events: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    x_bins: int = 6,
    y_bins: int = 3,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    show_stats: bool = True,
    cmap=None,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Zone heatmap (see :mod:`wa_setpieces.core.zones`) of event counts.

    Any events DataFrame works -- pass a filtered/extracted set (e.g.
    :func:`~wa_setpieces.extract_corners`) to see where a specific
    set-piece type happens most often. Defaults to the single-hue
    sequential blue ramp (counts are a magnitude, not a category).
    ``vertical=True`` draws on a goal-at-top :class:`mplsoccer.VerticalPitch`
    instead of the default horizontal one. ``show_stats=True`` (default)
    adds an auto-computed headline stat strip -- the total count and what
    share of it landed in the single busiest zone, e.g. "62% in one zone"
    as a direct, immediate answer to "how concentrated is this."
    """
    import matplotlib.patheffects as path_effects

    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)
    cmap = cmap if cmap is not None else pal.sequential_blue_cmap()

    x = pd.to_numeric(events[x_col], errors="coerce")
    y = pd.to_numeric(events[y_col], errors="coerce")
    valid = x.notna() & y.notna()

    binned = pitch.bin_statistic(x[valid], y[valid], statistic="count", bins=(x_bins, y_bins))
    pitch.heatmap(binned, ax=ax, cmap=cmap, edgecolor=pal.surface)
    labels = pitch.label_heatmap(
        binned, ax=ax, str_format="{:.0f}", color=pal.ink_primary, fontsize=11,
        ha="center", va="center",
    )
    stroke_color = "black" if dark else "white"
    for label in labels:
        label.set_path_effects(
            [path_effects.Stroke(linewidth=2.5, foreground=stroke_color), path_effects.Normal()]
        )
    header_stats = None
    total = int(binned["statistic"].sum())
    if show_stats and total:
        peak_share = binned["statistic"].max() / total
        header_stats = [(str(total), "total"), (f"{peak_share * 100:.0f}%", "in busiest zone")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_zone_scatter(
    events: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    outcome_col: str = "outcome",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    density: bool = True,
    show_stats: bool = True,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Every event as its own point, colored by outcome, optionally shaded
    by kernel density underneath -- the individual-event alternative to
    :func:`plot_zone_heatmap`'s binned grid.

    A grid answers "how many landed in this rectangle"; this answers
    "where exactly, and did it work" -- no binning choice (``x_bins``/
    ``y_bins``) implicitly deciding how coarse the picture is, and outcome
    is visible per point instead of only as an aggregate count. Reach for
    the grid when you want exact per-zone counts to read off; reach for
    this when the *shape* of where things land, and whether they worked,
    is the point.

    Args:
        outcome_col: column read as success (``== 1``) vs. not, same
            convention as :func:`plot_delivery_map`. Any events frame
            works, not just deliveries -- pass end coordinates
            (``x_col="end_x", y_col="end_y"``) to plot landing spots.
        density: shade a kernel-density estimate underneath the points
            (on by default here, unlike :func:`plot_delivery_map` --
            landing-spot density is meaningful even from a single match's
            worth of points, since there's no directional arrow implying
            more precision than the data has).
        show_stats: auto-computed count and success-rate stat strip,
            computed from ``events`` itself.

    Returns:
        ``(fig, ax)``.
    """
    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    x = pd.to_numeric(events[x_col], errors="coerce")
    y = pd.to_numeric(events[y_col], errors="coerce")
    valid = x.notna() & y.notna()
    valid_events = events[valid]
    x, y = x[valid], y[valid]

    if density and len(valid_events) >= 5:
        pitch.kdeplot(
            x, y, ax=ax, cmap=pal.sequential_blue_cmap(),
            fill=True, levels=8, thresh=0.05, alpha=0.5, zorder=1,
        )

    success = valid_events[outcome_col] == 1
    if (~success).any():
        pitch.scatter(
            x[~success], y[~success], ax=ax, color=pal.critical, s=90, alpha=0.85,
            edgecolors=pal.ink_primary, linewidths=0.6, zorder=3, label="Unsuccessful",
        )
    if success.any():
        pitch.scatter(
            x[success], y[success], ax=ax, color=pal.good, s=90, alpha=0.9,
            edgecolors=pal.ink_primary, linewidths=0.6, zorder=4, label="Successful",
        )

    pal.style_legend(ax)
    header_stats = None
    if show_stats and len(valid_events):
        header_stats = [
            (str(len(valid_events)), "events"),
            (f"{success.mean() * 100:.0f}%", "success rate"),
        ]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_xt_grid(
    model,
    title: str | None = "Expected Threat (xT) grid",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    cmap=None,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Heatmap of a fitted :class:`~wa_setpieces.XTModel` grid.

    Defaults to the single-hue sequential green ramp -- a second magnitude
    scale, kept visually distinct from :func:`plot_zone_heatmap`'s blue so
    the two can sit side by side (e.g. in :func:`plot_dashboard`) without
    implying they're the same quantity. Brighter cells are worth more xT --
    should climb steadily towards the opponent's goal (``x=100``).
    """
    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)
    cmap = cmap if cmap is not None else pal.sequential_green_cmap()

    import matplotlib.patheffects as pe

    stats = pitch.bin_statistic(
        [50.0], [50.0], statistic="count", bins=(model.x_bins, model.y_bins)
    )
    stats["statistic"] = model.grid
    mesh = pitch.heatmap(stats, ax=ax, cmap=cmap, edgecolor=pal.surface)
    pitch.label_heatmap(
        stats, ax=ax, str_format="{:.3f}", color=pal.ink_primary, fontsize=8, fontweight="bold",
        ha="center", va="center", exclude_zeros=False,
        path_effects=[pe.withStroke(linewidth=2, foreground=pal.surface)],
    )
    if fig is not None:
        cbar = fig.colorbar(mesh, ax=ax, fraction=0.035, pad=0.02)
        cbar.ax.tick_params(colors=pal.ink_secondary, labelsize=8)
        cbar.outline.set_edgecolor(pal.gridline)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_second_phase(
    events: pd.DataFrame,
    delivery_event_id: int,
    contestant_id: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    ax=None,
    pitch_kwargs: dict | None = None,
    **phase_kwargs,
):
    """Visualize one corner/free-kick's delivery and its phase-window events.

    Draws the delivery as a solid arrow, then each subsequent touch in the
    phase window as a numbered, faded marker so you can follow the passage
    of play. The second-phase shot (if any) is highlighted in gold (the
    same "this is a goal-adjacent moment" accent used for goals elsewhere).

    Args:
        delivery_event_id: the ``eventId`` of a corner or free-kick delivery
            (as returned by :func:`~wa_setpieces.extract_corners` /
            :func:`~wa_setpieces.extract_free_kicks`). ``eventId`` is only
            unique *within one team's own event stream* (both teams number
            their events 1, 2, 3, ... independently), so this is resolved
            against corner/free-kick deliveries specifically rather than
            all events, and raises if that's still ambiguous -- pass
            ``contestant_id`` to disambiguate when it is.
        contestant_id: required if ``delivery_event_id`` matches more than
            one corner/free-kick delivery (rare, but not impossible).
        **phase_kwargs: forwarded to :func:`wa_setpieces.core.phases.classify_phase`
            (e.g. ``clear_safe_x``, ``max_gap_seconds``).
    """
    from ..core.filters import extract_corners, extract_free_kicks
    from ..core.phases import _phase_window, _seconds, classify_phase
    from ..core.zones import to_reference_frame

    pal = theme.get_palette(dark)

    corners = extract_corners(events).assign(set_piece_type="corner")
    free_kicks = extract_free_kicks(events).assign(set_piece_type="free_kick")
    # classify_phase reads `set_piece_type` straight off the delivery row
    # when present -- extract_corners/extract_free_kicks don't tag it
    # themselves, so without this the title's set-piece-type fell back to
    # the generic "set piece" every time, never actually "corner" or
    # "free kick".
    candidates = pd.concat([corners, free_kicks])
    matches = candidates[candidates["eventId"] == delivery_event_id]
    if contestant_id is not None:
        matches = matches[matches["contestantId"] == contestant_id]
    if matches.empty:
        raise ValueError(
            f"No corner or free-kick delivery with eventId={delivery_event_id}"
            + (f" and contestantId={contestant_id!r}" if contestant_id else "")
            + " found."
        )
    if len(matches) > 1:
        raise ValueError(
            f"eventId={delivery_event_id} matches {len(matches)} corner/free-kick "
            f"deliveries (eventId is only unique per team in this feed) -- pass "
            f"contestant_id to disambiguate."
        )
    delivery_row = matches.iloc[0]
    result = classify_phase(events, delivery_row, **phase_kwargs)
    attacking_team = delivery_row["contestantId"]

    pos = events.index.get_loc(delivery_row.name)
    window = _phase_window(
        events,
        pos + 1,
        delivery_row["periodId"],
        _seconds(delivery_row),
        phase_kwargs.get("max_gap_seconds", 8.0),
        phase_kwargs.get("max_total_seconds", 20.0),
        phase_kwargs.get("max_events", 25),
    )
    # Events in `window` may belong to either team, and Opta expresses x/y in
    # each event's own team's attacking direction (see zones.to_reference_frame)
    # -- mirror the defending team's events onto the attacking team's frame so
    # everything lands on one consistent shared pitch picture.
    if not window.empty:
        window = to_reference_frame(window, attacking_team)

    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    pitch.arrows(
        [delivery_row["x"]], [delivery_row["y"]],
        [window.iloc[0]["x"]] if not window.empty else [delivery_row["x"]],
        [window.iloc[0]["y"]] if not window.empty else [delivery_row["y"]],
        ax=ax, color=pal.ink_primary, width=2.5, headwidth=7, label="Delivery",
    )

    # A goalmouth scramble often has several touches within a couple of
    # pitch units of each other -- plotted at their literal coordinates
    # they'd stack into one unreadable blob of numbers, so nearby points
    # are nudged apart onto a small circle around their own true spot
    # rather than moved to some averaged position.
    touch_x, touch_y = _declutter_points(
        list(window["x"]) if not window.empty else [], list(window["y"]) if not window.empty else []
    )

    labeled_touch, labeled_shot = False, False
    for i, (_, row) in enumerate(window.iterrows()):
        is_second_phase_shot = row["eventId"] == result.second_phase_event_id
        color = pal.gold if is_second_phase_shot else pal.ink_muted
        size = 260 if is_second_phase_shot else 140
        label = None
        if is_second_phase_shot and not labeled_shot:
            label, labeled_shot = "Second-phase shot", True
        elif not is_second_phase_shot and not labeled_touch:
            label, labeled_touch = "Touch", True
        pitch.scatter(
            touch_x[i], touch_y[i], ax=ax, color=color, s=size,
            edgecolors=pal.ink_primary, zorder=3, label=label,
        )
        text_color = "black" if is_second_phase_shot else pal.ink_primary
        ax.annotate(
            str(i + 1), (touch_x[i], touch_y[i]), color=text_color, fontsize=8,
            ha="center", va="center", zorder=4,
        )

    pal.style_legend(ax)
    outcome = (
        "second-phase shot" if result.second_phase_shot
        else "cleared" if result.cleared_immediately
        else "no clear resolution"
    )
    if title is None:
        title = f"{(result.set_piece_type or 'set piece').replace('_', ' ').title()} sequence"
    if subtitle is None:
        subtitle = f"eventId {delivery_event_id} · {outcome}"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_team_comparison(
    summary: pd.DataFrame,
    metric: str = "attempts",
    team_names: dict | None = None,
    team_order: list | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Grouped horizontal bar chart comparing (up to two) teams across set-piece types.

    Args:
        summary: output of :func:`~wa_setpieces.team_set_piece_counts` or
            :func:`~wa_setpieces.set_piece_summary` -- needs ``contestantId``,
            ``set_piece_type`` and the ``metric`` column.
        metric: which column to plot, e.g. ``"attempts"``, ``"success_rate"``,
            ``"goals"``.
        team_names: optional ``{contestantId: display name}`` to label bars;
            defaults to a truncated ``contestantId``.
        team_order: optional ``[contestantId, ...]`` fixing which team gets
            the first (teal) team-color slot -- otherwise it falls out of
            row order in ``summary``, which isn't meaningful. Pass this
            whenever "our team" should consistently be the same color
            across a set of charts (see :func:`plot_dashboard`).

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    teams = team_order if team_order is not None else list(summary["contestantId"].drop_duplicates())
    if len(teams) > 2:
        raise ValueError(
            f"plot_team_comparison supports at most 2 teams, got {len(teams)}; "
            "filter `summary` first."
        )
    types = list(dict.fromkeys(summary["set_piece_type"]))
    y = np.arange(len(types))
    bar_height = 0.36

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.9 * len(types) + 1.2))

    fmt = "%.2f" if metric.endswith("_rate") else "%.0f"
    for i, team in enumerate(teams):
        team_rows = summary[summary["contestantId"] == team].set_index("set_piece_type")
        values = [team_rows[metric].get(t, 0) for t in types]
        offset = (i - (len(teams) - 1) / 2) * bar_height
        label = (team_names or {}).get(team, f"{team[:8]}…")
        bars = ax.barh(
            y + offset, values, height=bar_height * 0.92,
            color=pal.team_colors[i], label=label, zorder=3,
        )
        ax.bar_label(bars, fmt=fmt, color=pal.ink_secondary, fontsize=8, padding=3)

    ax.set_yticks(y)
    ax.set_yticklabels([t.replace("_", " ") for t in types], color=pal.ink_primary)
    ax.set_xlabel(metric.replace("_", " "))
    ax.invert_yaxis()
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    # upper right: the longest bars in practice (throw-ins) sit at the
    # bottom of the chart, so this is the corner least likely to collide --
    # verified against the sample match, where lower right clipped into the
    # throw-in bars.
    pal.style_legend(ax, loc="upper right")
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_volume_quality_scatter(
    data: pd.DataFrame,
    x_col: str = "attempts",
    y_col: str = "success_rate",
    label_col: str = "set_piece_type",
    labels: dict | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Quadrant scatter: one labeled point per row, ``x_col`` (volume) against
    ``y_col`` (quality) -- median reference lines split the plane into four
    quadrants (e.g. top-right is "does it a lot, and it works").

    A bar chart answers one metric at a time; this answers the question a
    bar chart can't -- does *volume* actually buy *quality*, or is the
    type/team with the most attempts also the least effective one.

    Args:
        data: any table with ``label_col``, ``x_col`` and ``y_col`` --
            :func:`~wa_setpieces.set_piece_summary`/
            :func:`~wa_setpieces.team_set_piece_counts` filtered to one
            team (points = set-piece types) or one type (points = teams)
            both work unchanged.
        label_col: which column identifies each point, and colors it --
            one categorical color per distinct value, in
            :data:`~wa_setpieces.viz.theme.CATEGORICAL` order.
        labels: optional ``{label_col value: display text}``.

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 6))

    rows = data.dropna(subset=[x_col, y_col])
    x_med, y_med = rows[x_col].median(), rows[y_col].median()

    for i, (_, row) in enumerate(rows.iterrows()):
        color = pal.categorical[i % len(pal.categorical)]
        ax.scatter(
            row[x_col], row[y_col], s=180, color=color, edgecolors=pal.ink_primary,
            linewidths=0.8, zorder=3,
        )
        label_value = row[label_col]
        display = (labels or {}).get(label_value, str(label_value).replace("_", " "))
        ax.annotate(
            display, (row[x_col], row[y_col]), xytext=(8, 6), textcoords="offset points",
            color=pal.ink_primary, fontsize=9, fontweight="bold", zorder=4,
        )

    ax.axvline(x_med, color=pal.baseline, linewidth=1, linestyle="--", zorder=1)
    ax.axhline(y_med, color=pal.baseline, linewidth=1, linestyle="--", zorder=1)
    ax.set_xlabel(x_col.replace("_", " "))
    ax.set_ylabel(y_col.replace("_", " "))
    ax.grid(color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    x_pad = max((rows[x_col].max() - rows[x_col].min()) * 0.15, 0.5)
    ax.set_xlim(rows[x_col].min() - x_pad, rows[x_col].max() + x_pad)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_xt_added_bars(
    delivery_xt: pd.DataFrame,
    value_col: str = "xt_added",
    label_col: str = "playerName",
    top_n: int = 15,
    title: str | None = "xT added per delivery",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Diverging bar chart of a signed per-delivery value (positive vs. negative).

    Works for either :func:`~wa_setpieces.core.xt.set_piece_delivery_xt`'s
    ``xt_added`` (the default) or :func:`~wa_setpieces.core.value.set_piece_added_value`'s
    ``added_value`` -- pass ``value_col="added_value"`` for the latter, which
    also folds in shot quality and goals, not just the delivery itself.

    Args:
        delivery_xt: a DataFrame with an ``eventId`` column and a signed
            numeric ``value_col``.
        value_col: which column holds the signed value to plot.
        label_col: column to label each bar with (``playerName`` by default).
        top_n: keep only the N deliveries with the largest ``|value_col|``
            (rows where ``value_col`` is NaN are dropped first).

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    valid = delivery_xt.dropna(subset=[value_col]).copy()
    valid = valid.reindex(valid[value_col].abs().sort_values(ascending=False).index)
    valid = valid.head(top_n).sort_values(value_col)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.4 * len(valid) + 1.5))

    colors = [pal.diverging_positive if v >= 0 else pal.diverging_negative
              for v in valid[value_col]]
    import matplotlib.patheffects as pe

    y = np.arange(len(valid))
    ax.barh(y, valid[value_col], color=colors, zorder=3)
    # Labeled just inside each bar's own tip, not with `bar_label`'s
    # default outside placement -- for the single longest bar (the whole
    # point of a top-N-by-magnitude chart) that default position lands
    # right at the axes' own edge, where it collides with that same row's
    # y-tick category label. Inside-the-bar placement can never collide
    # with anything outside the bar itself, and the stroke keeps it
    # legible over both bar colors and any background it slightly spills
    # onto for a very short bar.
    for yi, v in zip(y, valid[value_col]):
        ha = "right" if v >= 0 else "left"
        offset = -abs(v) * 0.04 if v >= 0 else abs(v) * 0.04
        ax.annotate(
            f"{v:.3f}", (v + offset, yi), color=pal.ink_primary, fontsize=8, fontweight="bold",
            ha=ha, va="center", zorder=4,
            path_effects=[pe.withStroke(linewidth=2, foreground=pal.surface)],
        )
    ax.axvline(0, color=pal.baseline, linewidth=1)
    labels = valid[label_col].fillna(valid["eventId"].astype(str)) if label_col in valid else valid["eventId"]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=pal.ink_primary, fontsize=9)
    ax.set_xlabel(value_col.replace("_", " "))
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_rating_benchmark(
    rated: pd.DataFrame,
    label_col: str = "contestantId",
    names: dict | None = None,
    top_n: int | None = None,
    title: str | None = "Rating benchmark",
    subtitle: str | None = "50 = sample average",
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Horizontal benchmark chart for a :mod:`wa_setpieces.core.rating`
    table (:func:`~wa_setpieces.core.rating.team_rating` or
    :func:`~wa_setpieces.core.rating.player_rating`): one bar per row,
    diverging from the sample-average baseline of 50 -- see that module's
    docstring: 50 means "average of whoever's in this table," not a
    universal benchmark, so this chart is only as meaningful as the peer
    group in ``rated``.

    Args:
        rated: a table with a ``rating`` column (0-100) and ``label_col``.
            Rows with a NaN ``rating`` (e.g. a player rated on neither
            delivery nor finishing) are dropped.
        label_col: which column identifies each row (``contestantId`` for
            :func:`~wa_setpieces.core.rating.team_rating`, ``playerName``
            for :func:`~wa_setpieces.core.rating.player_rating`).
        names: optional ``{label_col value: display name}``, e.g. team
            names when ``label_col="contestantId"``.
        top_n: keep only the N highest-rated rows (``None`` keeps all).

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    valid = rated.dropna(subset=["rating"]).sort_values("rating", ascending=False)
    if top_n is not None:
        valid = valid.head(top_n)
    valid = valid.sort_values("rating")  # ascending so the best bar plots last (top of the chart)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.4 * len(valid) + 1.5))

    colors = [pal.diverging_positive if r >= 50 else pal.diverging_negative for r in valid["rating"]]
    y = np.arange(len(valid))
    bars = ax.barh(y, valid["rating"] - 50, left=50, color=colors, zorder=3)
    ax.bar_label(
        bars, labels=[f"{r:.1f}" for r in valid["rating"]],
        color=pal.ink_secondary, fontsize=8, padding=3,
    )
    ax.axvline(50, color=pal.baseline, linewidth=1)
    labels = valid[label_col].map(lambda v: (names or {}).get(v, v))
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=pal.ink_primary, fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("rating")
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_corner_sonar(
    deliveries: pd.DataFrame,
    title: str | None = "Corner sonar",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    show_stats: bool = True,
    ax=None,
):
    """Polar "sonar" plot of corner (or free-kick) delivery angle and distance.

    Each delivery is one point: angle is the direction from the restart spot
    to where the ball ended up, radius is how far it travelled. Colored by
    outcome (status, not team) exactly like :func:`plot_delivery_map`, so
    the two read consistently together. ``show_stats=True`` (default) adds
    an auto-computed count and success-rate stat strip, same as
    :func:`plot_delivery_map`.

    Requires a polar ``ax`` if you pass one in
    (``plt.subplots(subplot_kw={"projection": "polar"})``).
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    d = deliveries.dropna(subset=["end_x", "end_y"]).copy()
    dx = d["end_x"] - d["x"]
    dy = d["end_y"] - d["y"]
    angle = np.arctan2(dy, dx)
    radius = np.hypot(dx, dy)
    for outcome_val, label, color in ((1, "Successful", pal.good), (0, "Unsuccessful", pal.critical)):
        mask = d["outcome"] == outcome_val
        if mask.any():
            ax.scatter(
                angle[mask], radius[mask], color=color, s=90, edgecolors=pal.ink_primary,
                linewidths=0.8, zorder=3, label=label,
            )
    ax.set_facecolor(pal.surface)
    ax.set_theta_zero_location("E")
    ax.tick_params(colors=pal.ink_secondary)
    ax.spines["polar"].set_color(pal.gridline)
    ax.grid(color=pal.gridline)
    if d["outcome"].notna().any():
        pal.style_legend(ax, loc="lower left", bbox_to_anchor=(-0.15, -0.1))
    header_stats = None
    if show_stats and len(d):
        success_rate = (d["outcome"] == 1).mean()
        header_stats = [(str(len(d)), "deliveries"), (f"{success_rate * 100:.0f}%", "success rate")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_match_timeline(
    events: pd.DataFrame,
    team_names: dict | None = None,
    title: str | None = "Set pieces through the match",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Swim-lane timeline of every set piece across the match.

    One row per set-piece type, one marker per delivery, positioned by
    match minute. Opta's ``timeMin`` already runs cumulatively across
    periods (period 2 starts at ~45, not 0 -- verified against
    ``tests/data/sample_match.json``, where period 1 spans timeMin 0-51 and
    period 2 spans 45-96), so it's used as-is with no per-period offset.
    Colored by team (teal then blue, the same two-team convention as
    :func:`plot_team_comparison`) -- the set-piece *type* is already
    encoded by row, so it doesn't need its own color too.
    """
    import matplotlib.pyplot as plt

    from ..core.constants import SET_PIECE_TYPES
    from ..core.filters import tag_set_pieces

    pal = theme.get_palette(dark)

    tagged = tag_set_pieces(events)
    sp = tagged[tagged["set_piece_type"].notna()].copy()
    sp["match_minute"] = pd.to_numeric(sp["timeMin"], errors="coerce")

    types = [t for t in SET_PIECE_TYPES if t in set(sp["set_piece_type"])]
    type_pos = {t: i for i, t in enumerate(types)}
    teams = list(sp["contestantId"].drop_duplicates())[:2]
    team_color = {team: pal.team_colors[i] for i, team in enumerate(teams)}

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 0.6 * len(types) + 1.5))

    for team in teams:
        team_rows = sp[sp["contestantId"] == team]
        y = team_rows["set_piece_type"].map(type_pos)
        label = (team_names or {}).get(team, f"{team[:8]}…")
        ax.scatter(
            team_rows["match_minute"], y, color=team_color[team], s=70,
            edgecolors=pal.ink_primary, linewidths=0.6, label=label, zorder=3,
        )

    for i in type_pos.values():
        ax.axhline(i, color=pal.gridline, linewidth=0.8, zorder=1)
    ax.axvline(45, color=pal.baseline, linewidth=1, linestyle="--", zorder=1, label="Half-time")

    ax.set_yticks(list(type_pos.values()))
    ax.set_yticklabels([t.replace("_", " ") for t in types], color=pal.ink_primary)
    ax.set_xlabel("Match minute")
    ax.invert_yaxis()
    pal.style_legend(ax, loc="upper right", ncol=1)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_set_piece_value_flow(
    events: pd.DataFrame,
    model,
    set_piece_types: tuple[str, ...] = ("corner", "free_kick"),
    team_names: dict | None = None,
    team_order: list | None = None,
    title: str | None = "Set-piece added value over the match",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    show_stats: bool = True,
    ax=None,
):
    """Cumulative set-piece added value, one step-line per team, over
    match time -- shows *when* threat was created, not just how much of
    it, the way a single end-of-match total can't.

    Only ``"corner"`` and ``"free_kick"`` have a wired-in value model
    (:func:`~wa_setpieces.core.value.set_piece_added_value`), so those
    are the two types combined by default -- narrow or widen
    ``set_piece_types`` to change that. Each delivery's ``timeMin`` is
    looked up from ``events`` scoped to ``(eventId, contestantId)``
    together, not ``eventId`` alone -- F24's ``eventId`` is only unique
    *within one team's own stream*, so an unscoped lookup would collide
    (see :doc:`../by_metric`'s "Linking to shots and goals" entry).

    Args:
        model: a fitted :class:`~wa_setpieces.XTModel`.
        team_order: optional ``[contestantId, ...]`` fixing which team
            gets the first (teal) line color, same convention as
            :func:`plot_team_comparison`.
        show_stats: auto-computed final cumulative value per team as the
            headline stat strip.

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    from ..core.value import set_piece_added_value

    pal = theme.get_palette(dark)

    frames = [set_piece_added_value(events, t, model) for t in set_piece_types]
    combined = (
        pd.concat(frames, ignore_index=True) if frames
        else pd.DataFrame(columns=["eventId", "contestantId", "added_value"])
    )
    time_lookup = events[["eventId", "contestantId", "timeMin"]].drop_duplicates(
        subset=["eventId", "contestantId"]
    )
    combined = combined.merge(time_lookup, on=["eventId", "contestantId"], how="left")

    teams = team_order if team_order is not None else list(combined["contestantId"].drop_duplicates())
    if len(teams) > 2:
        raise ValueError(
            f"plot_set_piece_value_flow supports at most 2 teams, got {len(teams)}; "
            "filter `events` first."
        )

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    final_values = []
    for i, team in enumerate(teams):
        rows = combined[combined["contestantId"] == team].sort_values("timeMin")
        t = [0, *rows["timeMin"].tolist()]
        cum = [0.0, *rows["added_value"].cumsum().tolist()]
        label = (team_names or {}).get(team, f"{team[:8]}…")
        ax.step(t, cum, where="post", color=pal.team_colors[i], linewidth=2.5, label=label, zorder=3)
        ax.fill_between(t, cum, step="post", color=pal.team_colors[i], alpha=0.12, zorder=2)
        final_values.append((label, cum[-1]))

    ax.axhline(0, color=pal.baseline, linewidth=1)
    ax.set_xlabel("Match minute")
    ax.set_ylabel("Cumulative added value")
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    pal.style_legend(ax, loc="upper left")
    _style_chart_axis(pal, ax)

    header_stats = None
    if show_stats and final_values:
        header_stats = [(f"{value:+.2f}", label) for label, value in final_values]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_dashboard(
    events: pd.DataFrame,
    team_id: str,
    set_piece_type: str = "corner",
    team_names: dict | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
):
    """One-figure set-piece report card for a team: delivery map, end-zone
    heatmap, and attempts/success-rate comparison against their opponent.

    Combines :func:`plot_delivery_map`, :func:`plot_zone_heatmap` and
    :func:`plot_team_comparison` into a single figure with
    :class:`matplotlib.gridspec.GridSpec`, in the spirit of a scouting
    report -- this is the "hero" figure to reach for over the individual
    plots when you want one shareable image. ``vertical=True`` draws the
    two pitch panels goal-at-top instead of goal-at-right -- the grid
    cells they sit in stay the same shape, so mplsoccer letterboxes a
    vertical pitch within that landscape-ish cell rather than the panel
    itself changing shape.

    Returns:
        ``fig`` (a new figure; there's no single ``ax`` to hand back).
    """
    import matplotlib.pyplot as plt

    from ..core.metrics import delivery_locations, set_piece_summary

    pal = theme.get_palette(dark)

    fig = plt.figure(figsize=(13, 9.5), facecolor=pal.surface)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=0.35, wspace=0.25)

    deliveries = delivery_locations(events, set_piece_type)
    team_deliveries = deliveries[deliveries["contestantId"] == team_id]
    label = (team_names or {}).get(team_id, f"{team_id[:8]}…")

    ax_map = fig.add_subplot(gs[0, 0])
    plot_delivery_map(
        team_deliveries, title=f"{label} — {set_piece_type} deliveries",
        dark=dark, vertical=vertical, ax=ax_map,
    )

    ax_heat = fig.add_subplot(gs[0, 1])
    plot_zone_heatmap(
        team_deliveries, x_col="end_x", y_col="end_y",
        title=f"{label} — {set_piece_type} end zones", dark=dark, vertical=vertical, ax=ax_heat,
    )

    summary = set_piece_summary(events)
    opponent_id = next(
        (t for t in summary["contestantId"].unique() if t != team_id), None
    )
    team_order = [team_id] + ([opponent_id] if opponent_id else [])
    both_teams = summary[summary["contestantId"].isin(team_order)]

    ax_attempts = fig.add_subplot(gs[1, 0])
    plot_team_comparison(
        both_teams, metric="attempts", team_names=team_names, team_order=team_order,
        title="Attempts by set-piece type", dark=dark, ax=ax_attempts,
    )

    ax_rate = fig.add_subplot(gs[1, 1])
    plot_team_comparison(
        both_teams, metric="success_rate", team_names=team_names, team_order=team_order,
        title="Success rate by set-piece type", dark=dark, ax=ax_rate,
    )

    header_stats = None
    team_row = summary[
        (summary["contestantId"] == team_id) & (summary["set_piece_type"] == set_piece_type)
    ]
    if not team_row.empty:
        row = team_row.iloc[0]
        header_stats = [
            (str(int(row["attempts"])), "attempts"),
            (f"{row['success_rate'] * 100:.0f}%", "success rate"),
            (str(int(row["goals"])), "goals"),
        ]

    pal.draw_header(
        fig, eyebrow=eyebrow, title=title or f"{label} — set-piece report",
        subtitle=subtitle, author=author, stats=header_stats,
    )
    pal.draw_footer(fig, source=footer, author=author)
    return fig


_DEFAULT_RADAR_METRICS = [
    "attempts",
    "success_rate",
    "second_phase_rate",
    "retention_rate",
    "avg_added_value",
]


def plot_set_piece_radar(
    report: pd.DataFrame,
    metrics: list[str] | None = None,
    team_names: dict | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Two-team radar comparing set-piece metrics, from :func:`~wa_setpieces.set_piece_report`.

    Built on :class:`mplsoccer.Radar`, which (unlike a hand-rolled polar
    plot) scales each spoke to its own min/max range -- necessary here
    since ``attempts`` (a raw count) and ``success_rate`` (0-1) aren't on
    the same scale.

    Args:
        report: exactly 2 rows, e.g. ``corner_report(events, model=model)``.
        metrics: which columns to plot as spokes. Defaults to whichever of
            ``attempts``, ``success_rate``, ``second_phase_rate``,
            ``retention_rate``, ``avg_added_value`` are present in
            ``report`` (``second_phase_rate``/``avg_added_value`` need
            ``second_phase_summary``/a fitted model to have been included).
        team_names: optional ``{contestantId: display name}``.

    Returns:
        ``(fig, ax)``.
    """
    from mplsoccer import Radar

    pal = theme.get_palette(dark)

    if len(report) != 2:
        raise ValueError(f"plot_set_piece_radar needs exactly 2 teams, got {len(report)}")

    metrics = metrics or [m for m in _DEFAULT_RADAR_METRICS if m in report.columns]
    if not metrics:
        raise ValueError(
            "no usable metric columns found in `report` -- pass `metrics` explicitly"
        )
    if len(metrics) < 3:
        raise ValueError(
            f"plot_set_piece_radar needs at least 3 metrics for a readable radar, "
            f"got {len(metrics)}: {metrics}"
        )

    row_a, row_b = report.iloc[0], report.iloc[1]
    values_a = [float(row_a[m]) for m in metrics]
    values_b = [float(row_b[m]) for m in metrics]

    min_range, max_range = [], []
    for m, va, vb in zip(metrics, values_a, values_b):
        if m.endswith("_rate"):
            min_range.append(0.0)
            max_range.append(1.0)
        else:
            # Auto-range with headroom, scaled to this metric's own span --
            # a fixed fallback range (e.g. 0-1) would flatten a small-magnitude
            # metric like avg_added_value (~0.01-0.02) to an invisible sliver.
            lo, hi = min(0.0, va, vb), max(0.0, va, vb)
            span = hi - lo
            if span == 0:
                span = max(abs(va), abs(vb), 1e-6)
                hi = lo + span
            pad = span * 0.15
            min_range.append(lo - pad if lo < 0 else lo)
            max_range.append(hi + pad)

    labels = [m.replace("_", " ").title() for m in metrics]
    radar = Radar(labels, min_range, max_range, num_rings=4, ring_width=1, center_circle_radius=1)

    fig = None
    if ax is None:
        fig, ax = radar.setup_axis(facecolor=pal.surface, figsize=(9, 9))
    else:
        radar.setup_axis(facecolor=pal.surface, ax=ax)

    radar.draw_circles(ax=ax, facecolor=pal.surface, edgecolor=pal.gridline)
    radar.draw_radar_compare(
        values_a, values_b, ax=ax,
        kwargs_radar={"facecolor": pal.team_colors[0], "alpha": 0.6},
        kwargs_compare={"facecolor": pal.team_colors[1], "alpha": 0.6},
    )
    radar.draw_range_labels(ax=ax, color=pal.ink_secondary, fontsize=9)
    radar.draw_param_labels(ax=ax, color=pal.ink_primary, fontsize=11)

    import matplotlib.patches as mpatches

    label_a = (team_names or {}).get(row_a["contestantId"], f"{row_a['contestantId'][:8]}…")
    label_b = (team_names or {}).get(row_b["contestantId"], f"{row_b['contestantId'][:8]}…")
    handles = [
        mpatches.Patch(color=pal.team_colors[0], label=label_a),
        mpatches.Patch(color=pal.team_colors[1], label=label_b),
    ]
    # loc="upper right" with no bbox_to_anchor keeps the legend inside the
    # axes' own bounding box (radar param labels leave the corners empty) --
    # placing it outside via bbox_to_anchor got silently clipped by any
    # savefig call that doesn't pass bbox_inches="tight" (e.g. sphinx-gallery's
    # default scraper), losing the text entirely.
    ax.legend(
        handles=handles, loc="upper right",
        facecolor=pal.surface, edgecolor="none", labelcolor=pal.ink_primary,
    )
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


_OUTCOME_LABELS = {
    "short_corner": "Short corner",
    "direct_shot": "Direct shot",
    "second_phase_shot": "Second-phase shot",
    "aerial_duel": "Aerial duel (50/50)",
    "cleared": "Cleared",
    "first_touch_lost": "First touch lost",
    "first_touch_won": "First touch won",
    "no_action": "No action",
}


def plot_set_piece_outcomes(
    outcomes: pd.DataFrame,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Shot-map-style scatter of corner/free-kick outcomes, from
    :func:`~wa_setpieces.core.outcomes.delivery_outcomes`.

    Each point is one delivery, colored by what happened right after it
    (see :mod:`wa_setpieces.core.outcomes` for the category definitions and
    where each category's point is placed -- e.g. the first-contact spot
    for a won/lost/aerial duel, the shot spot for a direct or second-phase
    shot). Deliveries that ended in a goal get a gold ring around the
    marker -- the same fixed goal accent used elsewhere in the package,
    distinct from both the category colors and the status colors.

    Colors follow the fixed categorical order in
    :data:`~wa_setpieces.core.outcomes.OUTCOME_CATEGORIES`, not the order
    categories happen to appear in this particular match, so the same
    category is always the same color across different plots. With up to
    8 categories in play, identity leans on the legend (direct labels),
    not on hue alone, per the palette's own rule for categorical sets
    past 4 series.
    """
    from ..core.outcomes import OUTCOME_CATEGORIES

    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    color_map = {cat: pal.categorical[i % len(pal.categorical)] for i, cat in enumerate(OUTCOME_CATEGORIES)}
    present = [cat for cat in OUTCOME_CATEGORIES if (outcomes["delivery_outcome"] == cat).any()]

    for cat in present:
        rows = outcomes[outcomes["delivery_outcome"] == cat]
        pitch.scatter(
            rows["x"], rows["y"], ax=ax, color=color_map[cat], s=110,
            edgecolors=pal.ink_primary, linewidths=0.7,
            label=_OUTCOME_LABELS.get(cat, cat), zorder=3,
        )

    goals = outcomes[outcomes["is_goal"]]
    if not goals.empty:
        pitch.scatter(
            goals["x"], goals["y"], ax=ax, facecolors="none",
            edgecolors=pal.gold, linewidths=2.5, s=240, zorder=4, label="Goal",
        )

    pal.style_legend(ax, loc="upper left", fontsize=8, ncol=1)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_routine_clusters(
    clustered: pd.DataFrame,
    title: str | None = "Routine clusters",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Arrow map of deliveries colored by data-driven cluster, from
    :func:`~wa_setpieces.core.routines.cluster_routines`.

    Each cluster gets its own categorical color and a legend entry labeled
    with its auto-generated ``cluster_label`` (e.g. "short, forward,
    central") rather than a bare cluster number. Deliveries left
    unclustered (``cluster == -1`` -- missing a feature value, or too few
    usable rows for the requested ``n_clusters``) are drawn muted so they
    don't compete with the categorical palette.
    """
    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    clusters = sorted(cid for cid in clustered["cluster"].unique() if cid >= 0)
    color_map = {cid: pal.categorical[i % len(pal.categorical)] for i, cid in enumerate(clusters)}

    unclustered = clustered[clustered["cluster"] < 0]
    if not unclustered.empty:
        pitch.arrows(
            unclustered["x"], unclustered["y"], unclustered["end_x"], unclustered["end_y"],
            ax=ax, color=pal.ink_muted, width=1.5, headwidth=5, alpha=0.5, label="Unclustered",
        )
    for cid in clusters:
        rows = clustered[clustered["cluster"] == cid]
        label = rows["cluster_label"].iloc[0] if not rows.empty else f"Cluster {cid}"
        pitch.arrows(
            rows["x"], rows["y"], rows["end_x"], rows["end_y"],
            ax=ax, color=color_map[cid], width=2, headwidth=6, alpha=0.9, label=label,
        )

    pal.style_legend(ax, fontsize=8)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_defensive_routine_bars(
    conceded: pd.DataFrame,
    metric: str = "attempts_faced",
    team_id: str | None = None,
    team_name: str | None = None,
    top_n: int = 8,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    show_stats: bool = True,
    ax=None,
):
    """Horizontal bar chart of what a team concedes most, by routine type or
    destination zone -- from
    :func:`~wa_setpieces.core.defending.defensive_routine_summary` or
    :func:`~wa_setpieces.core.defending.defensive_zone_summary`.

    Args:
        conceded: output of either function above (auto-detects which one
            by whether a ``routine_type`` or ``destination_zone`` column
            is present).
        metric: which column to plot -- ``"attempts_faced"`` (default),
            ``"shots_conceded"``, ``"goals_conceded"`` or
            ``"shot_rate_conceded"``.
        team_id: filter to one team; required if ``conceded`` covers more
            than one (both functions return every team by default).
        top_n: keep only the N highest-``metric`` rows.

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)

    group_col = "routine_type" if "routine_type" in conceded.columns else "destination_zone"
    rows = conceded
    if team_id is not None:
        rows = rows[rows["contestantId"] == team_id]
    elif rows["contestantId"].nunique() > 1:
        raise ValueError(
            "conceded covers more than one team -- pass team_id to pick which one to plot"
        )
    rows = rows.sort_values(metric, ascending=False).head(top_n).sort_values(metric)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.45 * len(rows) + 1.5))

    y = np.arange(len(rows))
    bars = ax.barh(y, rows[metric], color=pal.categorical[0], zorder=3)
    fmt = "%.2f" if metric.endswith("_rate") else "%.0f"
    ax.bar_label(bars, fmt=fmt, color=pal.ink_secondary, fontsize=8, padding=3)
    ax.set_yticks(y)
    ax.set_yticklabels([str(v).replace("_", " ") for v in rows[group_col]], color=pal.ink_primary)
    ax.set_xlabel(metric.replace("_", " "))
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    if title is None:
        title = f"Conceded by {group_col.replace('_', ' ')}"
    if subtitle is None:
        label = team_name or (f"{team_id[:8]}…" if team_id else "All teams")
        subtitle = f"Team {label}"
    _style_chart_axis(pal, ax)
    header_stats = None
    if show_stats and len(rows):
        top_row = rows.iloc[-1]
        header_stats = [
            (str(int(rows[metric].sum())) if not metric.endswith("_rate") else f"{rows[metric].mean():.2f}", metric.replace("_", " ")),
            (str(top_row[group_col]).replace("_", " "), "most exposed to"),
        ]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_aerial_duel_win_rate(
    team_summary: pd.DataFrame,
    team_names: dict | None = None,
    title: str | None = "Aerial duel win rate",
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Horizontal bar chart of aerial-duel win rate per team, from
    :func:`~wa_setpieces.core.outcomes.aerial_duel_summary`'s
    ``team_summary`` (the first of the two DataFrames it returns).

    Diverges from 50% the same way :func:`plot_rating_benchmark` diverges
    from a rating of 50, so the two read consistently together.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows = team_summary.sort_values("win_rate")

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 0.5 * len(rows) + 1.5))

    y = np.arange(len(rows))
    win_pct = rows["win_rate"] * 100
    colors = [pal.diverging_positive if v >= 50 else pal.diverging_negative for v in win_pct]
    bars = ax.barh(y, win_pct, color=colors, zorder=3)
    ax.bar_label(bars, fmt="%.0f%%", color=pal.ink_secondary, fontsize=8, padding=3)
    ax.axvline(50, color=pal.baseline, linewidth=1, linestyle="--")
    labels = [(team_names or {}).get(t, f"{t[:8]}…") for t in rows["contestantId"]]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=pal.ink_primary)
    ax.set_xlim(0, 100)
    ax.set_xlabel("win rate (%)")
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


_OUTCOME_FLOW_ORDER = [
    "short_corner", "direct_shot", "second_phase_shot", "aerial_duel",
    "first_touch_won", "first_touch_lost", "cleared", "no_action",
]


def plot_outcome_flow(
    outcomes: pd.DataFrame,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    show_stats: bool = True,
    ax=None,
):
    """Sankey-style flow of every delivery from the restart, through its
    :func:`~wa_setpieces.core.outcomes.delivery_outcomes` category, down to
    whether it ended in a goal.

    A genuinely different chart form from anything else in this module --
    no pitch, no bars, no scatter -- built for one question none of them
    answer directly: of everything that happens after a corner is taken,
    how much of it actually funnels through to a goal. In practice that's
    usually "very little," and the ribbon widths make that funnel visible
    at a glance in a way a table of category counts doesn't.

    Args:
        outcomes: output of :func:`~wa_setpieces.core.outcomes.delivery_outcomes`
            -- needs ``delivery_outcome`` and ``is_goal``.

    ``ax`` must not be passed for this one: the flow needs the whole
    figure's canvas (no meaningful x/y axes to share), so pass ``None``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows = outcomes.dropna(subset=["delivery_outcome"])
    total = len(rows)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5.6))

    present = [o for o in _OUTCOME_FLOW_ORDER if (rows["delivery_outcome"] == o).any()]
    colors = {o: pal.categorical[i % len(pal.categorical)] for i, o in enumerate(present)}
    node_w = 0.5
    x0, x1, x2 = 0.0, 4.5, 9.0

    stage1_ranges: dict[str, tuple[float, float]] = {}
    y = 0.0
    for o in present:
        n = int((rows["delivery_outcome"] == o).sum())
        stage1_ranges[o] = (y, y + n)
        y += n

    n_goal = int(rows["is_goal"].sum())
    n_nogoal = total - n_goal

    ax.add_patch(plt.Rectangle((x0, 0), node_w, total, facecolor=pal.ink_secondary, edgecolor="none", zorder=3))
    for o in present:
        y0, y1 = stage1_ranges[o]
        ax.add_patch(plt.Rectangle((x1, y0), node_w, y1 - y0, facecolor=colors[o], edgecolor="none", zorder=3))
        ax.text(
            x1 + node_w + 0.15, (y0 + y1) / 2, f"{o.replace('_', ' ')} ({y1 - y0:.0f})",
            va="center", ha="left", color=pal.ink_primary, fontsize=9,
        )
        _flow_ribbon(ax, x0 + node_w, x1, y0, y1, y0, y1, colors[o], zorder=2)

    ax.add_patch(plt.Rectangle((x2, 0), node_w, n_nogoal, facecolor=pal.ink_muted, edgecolor="none", zorder=3))
    ax.text(x2 + node_w + 0.15, n_nogoal / 2 if n_nogoal else 0, f"No goal ({n_nogoal})", va="center", ha="left", color=pal.ink_primary, fontsize=9)
    if n_goal:
        ax.add_patch(plt.Rectangle((x2, n_nogoal), node_w, n_goal, facecolor=pal.good, edgecolor="none", zorder=3))
        ax.text(x2 + node_w + 0.15, n_nogoal + n_goal / 2, f"Goal ({n_goal})", va="center", ha="left", color=pal.good, fontsize=9, fontweight="bold")

    cursor_nogoal, cursor_goal = 0.0, float(n_nogoal)
    for o in present:
        y0, y1 = stage1_ranges[o]
        sub = rows[rows["delivery_outcome"] == o]
        g = int(sub["is_goal"].sum())
        ng = len(sub) - g
        if ng:
            _flow_ribbon(ax, x1 + node_w, x2, y0, y0 + ng, cursor_nogoal, cursor_nogoal + ng, colors[o], alpha=0.4, zorder=2)
            cursor_nogoal += ng
        if g:
            _flow_ribbon(ax, x1 + node_w, x2, y0 + ng, y1, cursor_goal, cursor_goal + g, colors[o], alpha=0.85, zorder=2)
            cursor_goal += g

    for x, label in ((x0 + node_w / 2, "Deliveries"), (x1 + node_w / 2, "Outcome"), (x2 + node_w / 2, "Result")):
        ax.text(x, total * 1.03, label, va="bottom", ha="center", color=pal.ink_secondary, fontsize=9.5, fontweight="bold")

    ax.set_xlim(-0.2, x2 + node_w + 2.6)
    ax.set_ylim(-total * 0.03, total * 1.12)
    ax.axis("off")
    ax.set_facecolor(pal.surface)

    header_stats = None
    if show_stats and total:
        header_stats = [(str(total), "deliveries"), (f"{n_goal / total * 100:.0f}%", "ended in a goal")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_rating_beeswarm(
    rated: pd.DataFrame,
    metric_col: str = "rating",
    label_col: str = "playerName",
    team_col: str = "contestantId",
    team_names: dict | None = None,
    team_order: list | None = None,
    label_top_n: int = 3,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Beeswarm distribution of a per-player rating.

    Unlike :func:`plot_rating_benchmark`'s ranked bars, every player is one
    dot at its own position on the 0-100 scale, spread vertically only
    enough to avoid overlapping a close rating (a deterministic binned
    stack, see :func:`_beeswarm_offsets` -- not a random jitter, which can
    still collide, and not a physics packing, which is overkill for a
    squad-sized point count). Answers a different question than the bar
    chart: how *spread out* the group's ratings are -- one tight cluster,
    or a long tail -- not just each player's individual rank.

    Colored by team, the same teal/blue convention as
    :func:`plot_team_comparison` (pass ``team_order`` to fix which team
    gets teal).

    Args:
        rated: output of :func:`~wa_setpieces.core.rating.player_rating`
            (or any table with ``metric_col``, ``label_col``, ``team_col``).
        label_top_n: label the top-N dots by ``metric_col`` (``0`` labels
            none) -- labeling every dot in a dense swarm is unreadable.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows = rated.dropna(subset=[metric_col]).reset_index(drop=True)

    teams = team_order if team_order is not None else list(rows[team_col].drop_duplicates())
    if len(teams) > 2:
        raise ValueError(
            f"plot_rating_beeswarm supports at most 2 teams, got {len(teams)}; "
            "filter `rated` first."
        )
    team_color = {t: pal.team_colors[i] for i, t in enumerate(teams)}

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 3.6))

    x = rows[metric_col].to_numpy(dtype=float)
    y = _beeswarm_offsets(x, bin_width=2.5, spacing=0.22)
    colors = [team_color.get(t, pal.ink_muted) for t in rows[team_col]]
    ax.scatter(x, y, s=130, color=colors, edgecolors=pal.ink_primary, linewidths=0.8, zorder=3)

    if label_top_n > 0 and len(rows):
        top = rows.assign(_y=y).nlargest(min(label_top_n, len(rows)), metric_col)
        for _, row in top.iterrows():
            # Push the label further out in whichever direction the dot is
            # already displaced from the center line, rather than always
            # straight up -- straight-up collides with the next dot in a
            # tightly stacked bin (several equal ratings land close
            # together), while an outward push clears the cluster.
            dy = 14 if row["_y"] >= 0 else -14
            va = "bottom" if row["_y"] >= 0 else "top"
            ax.annotate(
                row[label_col], (row[metric_col], row["_y"]),
                xytext=(0, dy), textcoords="offset points", ha="center", va=va,
                color=pal.ink_primary, fontsize=9, fontweight="bold", zorder=4,
            )

    ax.axvline(50, color=pal.baseline, linewidth=1, linestyle="--", zorder=1)
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.6, 1.6)
    ax.set_yticks([])
    ax.set_xlabel(metric_col.replace("_", " "))
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=team_color[t],
                   label=(team_names or {}).get(t, f"{t[:8]}…"), markersize=8)
        for t in teams
    ]
    if handles:
        pal.style_legend(ax, handles=handles, loc="upper left")
    _style_chart_axis(pal, ax)
    for spine in ("top", "left", "right"):
        ax.spines[spine].set_visible(False)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_value_waterfall(
    events: pd.DataFrame,
    team_id: str,
    model,
    set_piece_types: tuple[str, ...] = ("corner", "free_kick"),
    team_name: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Waterfall decomposition of one team's total set-piece added value,
    by set-piece type -- corner, free kick, ... stepping to a final
    "Total" bar.

    Each type's own bar floats from wherever the running total already
    was (green if it added value, red if it cost value -- a type this
    team is actively bad at can show up as a genuine negative
    contribution, not just "less positive"), and the final bar shows
    where all of them land. A different question than
    :func:`plot_set_piece_value_flow`'s *when* value accumulated over
    the match: this shows *which restart type* it came from.

    Args:
        team_id: which team's deliveries to decompose.
        set_piece_types: which types to break out as their own step --
            only ``"corner"`` and ``"free_kick"`` have a value model (see
            :mod:`wa_setpieces.core.value`).
    """
    import matplotlib.pyplot as plt

    from ..core.value import set_piece_added_value as _added_value

    pal = theme.get_palette(dark)
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.8))

    values = []
    for t in set_piece_types:
        detail = _added_value(events, t, model)
        team_detail = detail[detail["contestantId"] == team_id]
        values.append(float(team_detail["added_value"].sum()))
    grand_total = sum(values)

    labels = [t.replace("_", " ") for t in set_piece_types] + ["Total"]
    bottoms, heights = [], []
    running = 0.0
    for v in values:
        bottoms.append(min(running, running + v))
        heights.append(abs(v))
        running += v
    bottoms.append(min(0.0, grand_total))
    heights.append(abs(grand_total))

    colors = [pal.good if v >= 0 else pal.critical for v in values] + [pal.accent]
    x = np.arange(len(labels))
    ax.bar(x, heights, bottom=bottoms, color=colors, width=0.6, zorder=3)

    running = 0.0
    for i, v in enumerate(values):
        ax.plot([i + 0.3, i + 1 - 0.3], [running + v, running + v], color=pal.gridline, linewidth=1, zorder=2)
        running += v

    for i, v in enumerate([*values, grand_total]):
        top = bottoms[i] + heights[i]
        ax.text(i, top + abs(grand_total or 1) * 0.03, f"{v:+.3f}" if i < len(values) else f"{v:.3f}",
                 ha="center", va="bottom", color=pal.ink_primary, fontsize=9, fontweight="bold")

    ax.axhline(0, color=pal.baseline, linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=pal.ink_primary)
    ax.set_ylabel("added value")
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    if subtitle is None:
        subtitle = f"Team {team_name or (team_id[:8] + '…')}"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_value_distribution(
    events: pd.DataFrame,
    model,
    set_piece_types: tuple[str, ...] = ("corner", "free_kick"),
    value_col: str = "added_value",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Violin plot of per-delivery added value, one violin per set-piece
    type.

    Shows the *spread* a bar-chart average can't: a wide violin is a
    type that's either brilliant or costly depending on the delivery, a
    tight one is consistently middling. Built on matplotlib's
    ``violinplot``, restyled to the WA palette (categorical fill per
    type, a plain median line rather than the default box overlay).

    Args:
        set_piece_types: types to include, each needs >= 2 deliveries
            with a non-null ``value_col`` to form a violin -- types with
            fewer are silently skipped (a violin needs a real
            distribution to estimate, not one or two points).
    """
    import matplotlib.pyplot as plt

    from ..core.value import set_piece_added_value as _added_value

    pal = theme.get_palette(dark)
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.8))

    data, labels = [], []
    for t in set_piece_types:
        detail = _added_value(events, t, model)
        vals = detail[value_col].dropna().to_numpy()
        if len(vals) < 2:
            continue
        data.append(vals)
        labels.append(t.replace("_", " "))
    if not data:
        raise ValueError(
            "None of the given set_piece_types has enough deliveries "
            "(>= 2) to plot a distribution."
        )

    parts = ax.violinplot(data, showmeans=False, showmedians=True, widths=0.7)
    for i, body in enumerate(parts["bodies"]):
        color = pal.categorical[i % len(pal.categorical)]
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.55)
    for key in ("cbars", "cmins", "cmaxes", "cmedians"):
        if key in parts:
            parts[key].set_color(pal.ink_primary)
            parts[key].set_linewidth(1.2)

    ax.axhline(0, color=pal.baseline, linewidth=1, linestyle="--", zorder=1)
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels, color=pal.ink_primary)
    ax.set_ylabel(value_col.replace("_", " "))
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_type_radial_bar(
    summary: pd.DataFrame,
    team_id: str | None = None,
    metric: str = "attempts",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Radial ("wind-rose") bar chart of one metric across set-piece
    types -- one bar per type, arranged clockwise from the top instead of
    along a shared axis.

    A different read than :func:`plot_team_comparison`'s horizontal
    bars: every type gets equal visual weight around the circle
    regardless of label length or value, and it reads as a *shape* -- a
    team's restart profile -- rather than a ranking.

    Args:
        summary: output of :func:`~wa_setpieces.set_piece_summary` (or
            :func:`~wa_setpieces.team_set_piece_counts`).
        team_id: filter to one team; ``None`` sums ``metric`` across both
            (only sensible for an additive metric like ``attempts``,
            ``shots``, or ``goals`` -- not ``success_rate``, which can't
            be meaningfully summed across teams).

    Requires a polar ``ax`` if you pass one in
    (``plt.subplots(subplot_kw={"projection": "polar"})``).
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows = summary if team_id is None else summary[summary["contestantId"] == team_id]
    if team_id is None:
        rows = rows.groupby("set_piece_type", as_index=False)[metric].sum()

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw={"projection": "polar"})

    types = list(rows["set_piece_type"])
    values = [float(v) for v in rows[metric]]
    n = len(types)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    colors = [pal.categorical[i % len(pal.categorical)] for i in range(n)]
    ax.bar(angles, values, width=2 * np.pi / n * 0.85, color=colors, edgecolor=pal.surface, linewidth=1.5, zorder=3)

    import matplotlib.patheffects as pe

    is_pct = metric.endswith("_rate")
    max_value = max(values) if values else 0.0
    for angle, value in zip(angles, values):
        label = f"{value * 100:.0f}%" if is_pct else f"{value:.0f}"
        # A minimum radius (not just "halfway up the bar") keeps labels
        # for small wedges from collapsing on top of each other near the
        # pole, where equal angular spacing between categories still
        # maps to almost no physical distance. A dark stroke behind
        # light text keeps it legible whether it lands inside a colored
        # bar or out over the plain background.
        label_r = max(value / 2, max_value * 0.14)
        ax.text(
            angle, label_r, label, ha="center", va="center",
            color=pal.ink_primary, fontsize=10, fontweight="bold", zorder=4,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=pal.surface)],
        )

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels([t.replace("_", " ") for t in types], color=pal.ink_primary, fontsize=9)
    ax.set_facecolor(pal.surface)
    ax.tick_params(colors=pal.ink_secondary)
    ax.spines["polar"].set_color(pal.gridline)
    ax.grid(color=pal.gridline)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_success_waffle(
    n_success: int,
    n_total: int,
    grid: tuple[int, int] = (10, 10),
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Waffle (icon-array) chart: ``n_success`` out of ``n_total`` filled
    squares in a ``grid`` (default 10x10, one square per percentage
    point).

    A part-to-whole chart for a single headline ratio -- e.g. corner
    success rate -- that reads as a proportion at a glance the way a
    percentage number or a thin progress bar doesn't; the visual weight
    of "78 out of 100 squares filled" lands differently than "78%" does
    in a stat strip.

    Args:
        n_success: numerator (e.g. successful deliveries).
        n_total: denominator (e.g. total deliveries).
        grid: ``(rows, cols)`` -- default 10x10 so each square is
            exactly one percentage point; a coarser grid (e.g. ``(5, 4)``
            for small counts) reads better when ``n_total`` is small.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows, cols = grid
    n_cells = rows * cols
    filled = round(n_success / n_total * n_cells) if n_total else 0

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))

    for i in range(n_cells):
        r, c = divmod(i, cols)
        color = pal.good if i < filled else pal.gridline
        ax.add_patch(plt.Rectangle((c, rows - 1 - r), 0.85, 0.85, facecolor=color, edgecolor="none", zorder=3))

    ax.set_xlim(-0.5, cols + 0.5)
    ax.set_ylim(-0.5, rows + 1.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(pal.surface)
    pct = n_success / n_total * 100 if n_total else 0.0
    ax.text(cols / 2, rows + 0.6, f"{pct:.0f}%", ha="center", va="bottom", color=pal.good, fontsize=26, fontweight="bold", zorder=4)

    header_stats = [(str(n_success), "successful"), (str(n_total), "attempts")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_type_outcome_mosaic(
    summary: pd.DataFrame,
    team_id: str | None = None,
    team_name: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Marimekko-style mosaic: set-piece type along the x-axis with each
    segment's *width* proportional to attempts, and within each segment a
    stacked block whose *height* splits successful from unsuccessful.

    Volume and quality in the same chart, which
    :func:`plot_team_comparison`'s bars and
    :func:`plot_volume_quality_scatter`'s points each only show one half
    of on their own: a type that's both a big wide slab (a lot of
    attempts) and mostly red (low success) is the one worth fixing first,
    and it's the single most visually obvious thing in the chart.

    Args:
        summary: output of :func:`~wa_setpieces.set_piece_summary` (or
            :func:`~wa_setpieces.team_set_piece_counts`) -- needs
            ``attempts`` and ``successful``.
        team_id: filter to one team; required if ``summary`` covers more
            than one.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    rows = summary if team_id is None else summary[summary["contestantId"] == team_id]
    if rows["contestantId"].nunique() > 1:
        raise ValueError(
            "summary covers more than one team -- pass team_id to pick which one to plot."
        )
    rows = rows.loc[rows["attempts"] > 0].sort_values("attempts", ascending=False).reset_index(drop=True)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5.4))

    total_attempts = rows["attempts"].sum()
    # A segment narrower than this can't fit a rotated label under it
    # without colliding with its neighbors, and can't fit a percentage
    # inside it either -- both are skipped for segments this thin rather
    # than left to overlap (this is exactly what happened to the sample
    # match's 1-2 attempt "corner"/"kick off" segments during
    # verification: their labels ran into each other).
    min_label_width = 0.05
    x = 0.0
    for _, row in rows.iterrows():
        width = row["attempts"] / total_attempts if total_attempts else 0.0
        rate = row["successful"] / row["attempts"] if row["attempts"] else 0.0
        ax.add_patch(plt.Rectangle((x, 0), width, rate, facecolor=pal.good, edgecolor=pal.surface, linewidth=1.5, zorder=3))
        ax.add_patch(plt.Rectangle((x, rate), width, 1 - rate, facecolor=pal.critical, edgecolor=pal.surface, linewidth=1.5, zorder=3))
        cx = x + width / 2
        label = f"{row['set_piece_type'].replace('_', ' ')} (n={int(row['attempts'])})"
        rotation = 0 if width >= min_label_width * 2.2 else 45
        ha = "center" if rotation == 0 else "right"
        ax.text(cx, -0.05, label, ha=ha, va="top", color=pal.ink_primary, fontsize=8.5,
                 fontweight="bold", rotation=rotation, rotation_mode="anchor")
        if width >= min_label_width:
            if rate > 0.12:
                ax.text(cx, rate / 2, f"{rate * 100:.0f}%", ha="center", va="center", color=pal.surface, fontsize=9, fontweight="bold")
            if 1 - rate > 0.12:
                ax.text(cx, rate + (1 - rate) / 2, f"{(1 - rate) * 100:.0f}%", ha="center", va="center", color=pal.surface, fontsize=9, fontweight="bold")
        x += width

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.24, 1.14)
    ax.axis("off")
    ax.set_facecolor(pal.surface)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=pal.good, label="Successful"),
        plt.Rectangle((0, 0), 1, 1, facecolor=pal.critical, label="Unsuccessful"),
    ]
    # Above the mosaic body (y > 1), not "upper right" inside it -- any
    # in-bounds corner can land on top of a real segment depending on
    # how many types there are and how their success rates split.
    pal.style_legend(ax, handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2)
    if title is None:
        title = "Set pieces by type and outcome"
    if subtitle is None:
        label = team_name or (f"{team_id[:8]}…" if team_id else None)
        subtitle = f"Team {label}" if label else None
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_team_parallel_coordinates(
    report: pd.DataFrame,
    metrics: list[str] | None = None,
    team_names: dict | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Parallel-coordinates profile comparison for exactly two teams --
    the same normalized-metric idea as :func:`plot_set_piece_radar`, on
    straight vertical axes instead of a circle.

    A radar's polar layout visually exaggerates whichever metric lands
    on an outer ring and compresses whichever lands near the center,
    purely from axis placement, not the data. Parallel axes give every
    metric equal visual weight, and turn "which team leads on which
    metric" into a left-to-right read of where the lines cross, instead
    of comparing two overlapping polygon shapes.

    Args:
        report: output of :func:`~wa_setpieces.corner_report` /
            ``free_kick_report`` (or any table with a ``contestantId``
            column plus numeric metric columns) -- needs exactly 2 rows.
        metrics: which columns to plot as axes; defaults to
            ``success_rate``, ``second_phase_rate``, ``retention_rate``,
            ``avg_added_value``, filtered to whichever are present with
            no missing values across both rows.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    if len(report) != 2:
        raise ValueError(f"plot_team_parallel_coordinates needs exactly 2 rows, got {len(report)}.")

    default_metrics = ["success_rate", "second_phase_rate", "retention_rate", "avg_added_value"]
    candidates = metrics if metrics is not None else default_metrics
    metrics = [m for m in candidates if m in report.columns and report[m].notna().all()]
    if len(metrics) < 2:
        raise ValueError(
            "Need at least 2 usable metrics (present in `report`, no missing "
            "values in either row) to plot."
        )

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(metrics))
    mins = report[metrics].min()
    spans = (report[metrics].max() - mins).replace(0, 1)

    for i in range(len(report)):
        row = report.iloc[i]
        norm = [(row[m] - mins[m]) / spans[m] for m in metrics]
        label = (
            (team_names or {}).get(row["contestantId"], f"{row['contestantId'][:8]}…")
            if "contestantId" in report.columns else f"Row {i}"
        )
        ax.plot(x, norm, "o-", color=pal.team_colors[i], linewidth=2.5, markersize=9, zorder=3, label=label)
        dy, va = (10, "bottom") if i == 0 else (-10, "top")
        for xi, m, nv in zip(x, metrics, norm):
            ax.annotate(
                f"{row[m]:.3f}", (xi, nv), xytext=(0, dy), textcoords="offset points",
                ha="center", va=va, color=pal.ink_primary, fontsize=8, fontweight="bold", zorder=4,
            )

    for xi in x:
        ax.axvline(xi, color=pal.gridline, linewidth=0.8, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("_", " ") for m in metrics], color=pal.ink_primary, fontsize=9)
    ax.set_yticks([])
    ax.set_xlim(-0.3, len(metrics) - 0.7)
    ax.set_ylim(-0.2, 1.25)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor(pal.surface)
    pal.style_legend(ax, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2)
    if title is None:
        title = "Team profile comparison"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_team_dumbbell(
    summary: pd.DataFrame,
    metric: str = "attempts",
    team_names: dict | None = None,
    team_order: list | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Dumbbell (Cleveland dot) chart: two teams' values per category as
    a connected pair of dots on a shared axis, one row per category.

    A cleaner read than :func:`plot_team_comparison`'s grouped bars for
    exactly two series: the connecting line makes the *gap* between
    teams the thing your eye measures directly, instead of comparing two
    bar lengths against a shared baseline.

    Args:
        summary: output of :func:`~wa_setpieces.set_piece_summary` (or
            :func:`~wa_setpieces.team_set_piece_counts`).
        team_order: as in :func:`plot_team_comparison` -- fixes which
            team gets the first (teal) color slot, otherwise it falls
            out of row order in ``summary``.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    teams = team_order if team_order is not None else list(summary["contestantId"].drop_duplicates())
    if len(teams) > 2:
        raise ValueError(
            f"plot_team_dumbbell supports at most 2 teams, got {len(teams)}; filter `summary` first."
        )

    types = list(dict.fromkeys(summary["set_piece_type"]))
    pivot = summary.pivot_table(index="set_piece_type", columns="contestantId", values=metric, aggfunc="sum").reindex(types)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.6 * len(types) + 1.5))

    y = np.arange(len(types))
    present_teams = [t for t in teams if t in pivot.columns]
    for yi, typ in zip(y, types):
        xs = [pivot.loc[typ, t] for t in present_teams]
        if len(xs) == 2:
            ax.plot(xs, [yi, yi], color=pal.gridline, linewidth=2, zorder=2)
    for i, t in enumerate(present_teams):
        label = (team_names or {}).get(t, f"{t[:8]}…")
        ax.scatter(pivot[t].reindex(types), y, s=150, color=pal.team_colors[i], edgecolors=pal.ink_primary, linewidths=1, zorder=3, label=label)

    ax.set_yticks(y)
    ax.set_yticklabels([t.replace("_", " ") for t in types], color=pal.ink_primary)
    ax.set_xlabel(metric.replace("_", " "))
    ax.grid(axis="x", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    # Padded above the topmost category, not left to an auto "best"
    # corner -- "best" doesn't know a scatter+line pair from empty space
    # until it's already drawn there, and did land squarely on top of a
    # real row during verification. A dedicated empty band above all the
    # actual rows (rather than anchoring the legend above the axes
    # bounding box, which fights the header's own top-margin reservation
    # and collided with the title instead) guarantees clear space
    # regardless of figure height.
    ax.set_ylim(y.min() - 0.7, y.max() + 1.15)
    ax.set_axisbelow(True)
    pal.style_legend(ax, loc="upper left")
    _style_chart_axis(pal, ax)
    if title is None:
        title = f"{metric.replace('_', ' ').title()} by set-piece type"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_zone_bubble(
    events: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    x_bins: int = 6,
    y_bins: int = 3,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    vertical: bool = False,
    show_stats: bool = True,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Zone counts as size-encoded bubbles on the pitch, instead of
    :func:`plot_zone_heatmap`'s color-encoded grid.

    Size is a more intuitive encoding than color for "how many" -- a
    reader compares two bubbles' areas without consulting a color-ramp
    legend at all -- though it trades away precision for zones with
    close counts, where eyeballing relative circle size is harder than
    reading a heatmap's exact color-to-value mapping. Each bubble is
    also labeled with its own count, so the trade-off costs nothing here.

    Args:
        events: any DataFrame with numeric ``x_col``/``y_col`` (e.g.
            :func:`~wa_setpieces.delivery_locations` output).
        x_bins, y_bins: zone grid resolution, as in
            :func:`~wa_setpieces.core.zones.zone_counts`.
    """
    import re

    from ..core.zones import zone_counts

    pal = theme.get_palette(dark)
    pitch, fig, ax = _draw_pitch(pal, ax, pitch_kwargs, vertical=vertical)

    counts = zone_counts(events, x_col=x_col, y_col=y_col, x_bins=x_bins, y_bins=y_bins)
    xs, ys, sizes = [], [], []
    for _, row in counts.iterrows():
        match = re.match(r"R(\d+)C(\d+)", row["zone"])
        r, c = int(match.group(1)), int(match.group(2))
        xs.append((c + 0.5) / x_bins * 100)
        ys.append((r + 0.5) / y_bins * 100)
        sizes.append(int(row["count"]))

    max_count = max(sizes) if sizes else 1
    scaled = [200 + (s / max_count) * 1800 for s in sizes]
    pitch.scatter(
        xs, ys, ax=ax, s=scaled, color=pal.accent, alpha=0.6, edgecolors=pal.ink_primary,
        linewidths=1, zorder=3,
    )
    for x, y, s in zip(xs, ys, sizes):
        pitch.annotate(
            str(s), (x, y), ax=ax, ha="center", va="center", color=pal.surface,
            fontsize=8, fontweight="bold", zorder=4,
        )

    header_stats = None
    if show_stats and sizes:
        header_stats = [(str(sum(sizes)), "events"), (str(len(sizes)), "zones used")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_kpi_bullet(
    value: float,
    target: float | None = None,
    bands: tuple[float, float] | None = None,
    max_value: float | None = None,
    label: str = "",
    value_fmt: str = "{:.0%}",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Compact bullet/KPI chart: one ratio as a thin horizontal bar
    against three qualitative background bands (poor/fair/good), with an
    optional target tick.

    Built for a dashboard strip -- several of these stacked read as a
    scorecard -- rather than one chart's worth of visual weight, which
    is what :func:`plot_success_waffle` gives the same kind of single
    ratio instead.

    Args:
        value: the actual value to plot.
        target: optional benchmark value, drawn as a vertical tick
            (colored green if ``value`` clears it, red if not).
        bands: ``(low, high)`` boundaries splitting ``0..max_value`` into
            poor / fair / good background regions; defaults to even
            thirds of ``max_value``.
        max_value: axis maximum; defaults to
            ``max(value, target or 0, 1.0) * 1.05``.
        label: row label, drawn above the bar.
        value_fmt: format string for the value annotation, e.g.
            ``"{:.2f}"`` for a non-percentage metric.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    max_value = max_value if max_value is not None else max(value, target or 0, 1.0) * 1.05
    low, high = bands if bands is not None else (max_value / 3, max_value * 2 / 3)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 2.3))

    band_colors = [
        theme._mix(pal.surface, pal.critical, 0.3),
        theme._mix(pal.surface, pal.gold, 0.3),
        theme._mix(pal.surface, pal.good, 0.3),
    ]
    for (b0, b1), color in zip([(0, low), (low, high), (high, max_value)], band_colors):
        ax.barh(0, b1 - b0, left=b0, height=0.7, color=color, zorder=1)
    ax.barh(0, value, height=0.28, color=pal.ink_primary, zorder=3)
    if target is not None:
        tick_color = pal.good if value >= target else pal.critical
        ax.plot([target, target], [-0.35, 0.35], color=tick_color, linewidth=3, zorder=4)

    if label:
        ax.text(0, 0.48, label, ha="left", va="bottom", color=pal.ink_primary, fontsize=11, fontweight="bold")
    ax.annotate(
        value_fmt.format(value), (value, 0), xytext=(8, 0), textcoords="offset points",
        ha="left", va="center", color=pal.ink_primary, fontsize=10, fontweight="bold", zorder=5,
    )
    ax.set_xlim(0, max_value)
    ax.set_ylim(-0.5, 0.7)
    ax.set_yticks([])
    ax.tick_params(colors=pal.ink_secondary)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor(pal.surface)
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_value_ridgeline(
    events: pd.DataFrame,
    model,
    set_piece_types: tuple[str, ...] = ("corner", "free_kick"),
    value_col: str = "added_value",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Ridgeline (joyplot) of per-delivery added value: one smooth
    density curve per set-piece type, stacked with each type's own row.

    A smoother read of the *shape* of a distribution than
    :func:`plot_value_distribution`'s violins -- multi-modal (two
    distinct clusters of outcomes) versus a single peak is easier to
    spot in a KDE curve than in a violin's mirrored outline. Needs more
    data to be trustworthy than a violin does, though: each type needs
    at least 3 deliveries with non-identical values, or it's silently
    skipped (a density estimate from 2 points is not a real shape).

    Args:
        set_piece_types: types to include, in top-to-bottom row order.
    """
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde

    from ..core.value import set_piece_added_value as _added_value

    pal = theme.get_palette(dark)

    series = []
    for t in set_piece_types:
        detail = _added_value(events, t, model)
        vals = detail[value_col].dropna().to_numpy()
        if len(vals) < 3 or np.ptp(vals) == 0:
            continue
        series.append((t, vals))
    if not series:
        raise ValueError(
            "None of the given set_piece_types has enough deliveries (>= 3, "
            "non-constant) to estimate a density."
        )

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 0.9 * len(series) + 2.2))

    all_vals = np.concatenate([v for _, v in series])
    pad = (all_vals.max() - all_vals.min()) * 0.1 or 1.0
    grid = np.linspace(all_vals.min() - pad, all_vals.max() + pad, 200)

    n = len(series)
    for i, (t, vals) in enumerate(series):
        y0 = (n - 1 - i) * 1.0
        density = gaussian_kde(vals)(grid)
        density = density / density.max() * 0.85
        color = pal.categorical[i % len(pal.categorical)]
        ax.fill_between(grid, y0, y0 + density, color=color, alpha=0.65, zorder=3 + i)
        ax.plot(grid, y0 + density, color=color, linewidth=1.5, zorder=3 + i)
        ax.axhline(y0, color=pal.gridline, linewidth=0.8, zorder=1)
        ax.text(
            grid[0], y0 + 0.08, f"{t.replace('_', ' ')} (n={len(vals)})", ha="left", va="bottom",
            color=pal.ink_primary, fontsize=9.5, fontweight="bold", zorder=4,
        )

    ax.axvline(0, color=pal.baseline, linewidth=1, linestyle="--", zorder=2)
    ax.set_xlim(grid[0], grid[-1])
    ax.set_ylim(0, n * 1.0 + 0.15)
    ax.set_yticks([])
    ax.set_xlabel(value_col.replace("_", " "))
    ax.xaxis.label.set_color(pal.ink_secondary)
    ax.tick_params(colors=pal.ink_secondary)
    for spine in ("top", "left", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(pal.gridline)
    ax.set_facecolor(pal.surface)
    if title is None:
        title = "Added value distribution shape"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_type_area_timeline(
    events: pd.DataFrame,
    bin_minutes: int = 15,
    team_id: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Stacked area chart of set-piece attempts over match time, binned
    into ``bin_minutes``-wide windows, one colored band per type.

    A cumulative-*volume* read of the match: which restart types made up
    the bulk of the traffic in each phase of the game, and whether that
    mix shifted -- a team leaning on throw-ins early, corners piling up
    late while chasing a goal. Different from
    :func:`plot_match_timeline`'s swim-lane dots (every individual
    event, unaggregated) and :func:`plot_set_piece_value_flow`'s
    cumulative line (one signed value, not a volume breakdown by type).

    Args:
        bin_minutes: width of each time window.
        team_id: filter to one team; ``None`` combines both.
    """
    import matplotlib.pyplot as plt

    from ..core.constants import SET_PIECE_TYPES
    from ..core.filters import tag_set_pieces

    pal = theme.get_palette(dark)
    tagged = tag_set_pieces(events)
    sp = tagged[tagged["set_piece_type"].notna()].copy()
    if team_id is not None:
        sp = sp[sp["contestantId"] == team_id]
    sp["match_minute"] = pd.to_numeric(sp["timeMin"], errors="coerce")
    sp = sp.dropna(subset=["match_minute"])

    types = [t for t in SET_PIECE_TYPES if t in set(sp["set_piece_type"])]
    if not types:
        raise ValueError("No set-piece events found to plot.")

    max_minute = sp["match_minute"].max()
    bin_edges = np.arange(0, max_minute + bin_minutes, bin_minutes)
    sp["bin"] = pd.cut(sp["match_minute"], bin_edges, right=False)
    counts = (
        sp.groupby(["bin", "set_piece_type"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=types, fill_value=0)
    )
    bin_centers = [interval.left + bin_minutes / 2 for interval in counts.index]

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    colors = [pal.categorical[i % len(pal.categorical)] for i in range(len(types))]
    bands = ax.stackplot(
        bin_centers, [counts[t] for t in types], labels=[t.replace("_", " ") for t in types],
        colors=colors, alpha=0.85, zorder=3,
    )
    # Two of the categorical colors happen to be adjacent shades of
    # orange -- fine spaced apart elsewhere, but with no gap between
    # touching stacked bands two neighboring types can blend into one
    # region (confirmed by rendering: "throw in"/"goal kick" were
    # indistinguishable without this). A stroke between every band
    # guarantees a visible seam regardless of which two colors happen to
    # land next to each other.
    for band in bands:
        band.set_edgecolor(pal.surface)
        band.set_linewidth(1.2)
    ax.set_xlabel("Match minute")
    ax.set_ylabel("Attempts")
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    pal.style_legend(ax, loc="upper left")
    _style_chart_axis(pal, ax)
    if title is None:
        title = "Set-piece volume through the match"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_success_ring(
    n_success: int,
    n_total: int,
    label: str = "",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """A single ratio as a circular progress ring (donut), instead of
    :func:`plot_success_waffle`'s grid of squares.

    A different visual metaphor for the same "one headline ratio" job --
    closer to what a KPI dashboard widget typically looks like -- for
    when a ring reads more naturally than a filled-square count in
    context (e.g. next to other ring-shaped gauges).

    Args:
        n_success: numerator (e.g. successful deliveries).
        n_total: denominator (e.g. total deliveries).
        label: caption drawn under the percentage, inside the ring.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    pct = n_success / n_total if n_total else 0.0

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(5.5, 5.5))

    ax.pie(
        [pct, 1 - pct] if n_total else [0, 1], colors=[pal.good, pal.gridline], startangle=90,
        counterclock=False, wedgeprops=dict(width=0.28, edgecolor=pal.surface, linewidth=2),
    )
    ax.text(0, 0.12, f"{pct * 100:.0f}%", ha="center", va="center", color=pal.ink_primary, fontsize=32, fontweight="bold", zorder=4)
    ax.text(0, -0.14, label or f"{n_success} / {n_total}", ha="center", va="center", color=pal.ink_muted, fontsize=11, zorder=4)

    header_stats = [(str(n_success), "successful"), (str(n_total), "attempts")]
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_half_comparison_slope(
    events: pd.DataFrame,
    metric: str = "attempts",
    team_id: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Slope chart: each set-piece type's value in the first half versus
    the second half, as a two-point connected line.

    A genuinely different temporal comparison than
    :func:`plot_set_piece_value_flow`'s continuous cumulative curve --
    this collapses the match down to exactly two snapshots and makes
    each type's *direction of change* (more or less of it after the
    break) the thing the eye reads directly from the line's slope,
    green for more, red for less.

    Args:
        metric: ``"attempts"`` or ``"success_rate"``.
        team_id: filter to one team; required if ``events`` covers more
            than one (mixing halves across two teams isn't meaningful).
    """
    import matplotlib.pyplot as plt

    from ..core.metrics import team_set_piece_counts

    pal = theme.get_palette(dark)
    ev = events if team_id is None else events[events["contestantId"] == team_id]
    if team_id is None and ev["contestantId"].nunique() > 1:
        raise ValueError(
            "events covers more than one team -- pass team_id to pick which one to plot."
        )

    first_half = ev[ev["periodId"] == 1]
    second_half = ev[ev["periodId"] == 2]
    s1 = team_set_piece_counts(first_half)
    s2 = team_set_piece_counts(second_half)

    types = sorted(set(s1["set_piece_type"]) | set(s2["set_piece_type"]))
    if not types:
        raise ValueError("No set-piece events found in either half.")

    def _value(summary, t):
        row = summary[summary["set_piece_type"] == t]
        if row.empty:
            return 0.0
        return float(row["attempts"].sum()) if metric == "attempts" else float(row[metric].iloc[0])

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.5, 0.7 * len(types) + 2.2))

    values = [(t, _value(s1, t), _value(s2, t)) for t in types]
    for t, v1, v2 in values:
        color = pal.ink_muted if v2 == v1 else (pal.good if v2 > v1 else pal.critical)
        ax.plot([0, 1], [v1, v2], "o-", color=color, linewidth=2.2, markersize=8, zorder=3)
        dy, va = (9, "bottom") if v1 <= v2 else (-9, "top")
        ax.annotate(
            t.replace("_", " "), (0, v1), xytext=(0, dy), textcoords="offset points",
            ha="center", va=va, color=pal.ink_primary, fontsize=8.5, fontweight="bold", zorder=4,
        )

    ax.set_xlim(-0.3, 1.3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["First half", "Second half"], color=pal.ink_primary, fontsize=10)
    ax.set_ylabel(metric.replace("_", " "))
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(pal.gridline)
    ax.spines["bottom"].set_color(pal.gridline)
    ax.tick_params(colors=pal.ink_secondary)
    ax.set_facecolor(pal.surface)
    if title is None:
        title = f"{metric.replace('_', ' ').title()} by half"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_delivery_combination_network(
    events: pd.DataFrame,
    set_piece_type: str,
    team_id: str,
    min_weight: int = 1,
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Node-link network of delivery combinations: which player usually
    takes a corner/free-kick, and which teammate usually wins the first
    contact.

    Built from :func:`~wa_setpieces.core.phases.classify_phase`'s own
    ``first_contact_*`` fields, scoped to first contacts won by the
    delivering team itself -- a defender winning it first isn't a
    "combination". Nodes (players) sit evenly around a circle; edge
    width is how often that taker-to-receiver pairing happened, node
    size is how often that player was involved at all, as either end.

    The first node-link graph in this module -- every other
    multi-entity chart here (radar, parallel coordinates, dumbbell)
    compares a fixed small set of teams or categories, not an open set
    of players connected by who-delivers-to-whom.

    Args:
        set_piece_type: ``"corner"`` or ``"free_kick"``.
        team_id: which team's combinations to plot.
        min_weight: drop pairings that happened fewer than this many
            times -- ``1`` (the default) keeps everything, useful for a
            single match; raise it for a season's worth of data where a
            one-off pairing is noise, not a pattern.
    """
    import matplotlib.pyplot as plt

    from ..core.filters import extract_corners, extract_free_kicks
    from ..core.phases import classify_phase

    pal = theme.get_palette(dark)
    extractor = {"corner": extract_corners, "free_kick": extract_free_kicks}[set_piece_type]
    deliveries = extractor(events)
    deliveries = deliveries[deliveries["contestantId"] == team_id]

    edges: dict[tuple[str, str], int] = {}
    node_count: dict[str, int] = {}
    for _, delivery_row in deliveries.iterrows():
        result = classify_phase(events, delivery_row)
        taker = delivery_row.get("playerName")
        if result.first_contact_event_id is None or result.first_contact_team != team_id:
            continue
        contact_row = events[
            (events["contestantId"] == team_id) & (events["eventId"] == result.first_contact_event_id)
        ]
        if contact_row.empty:
            continue
        receiver = contact_row.iloc[0].get("playerName")
        if not taker or not receiver or taker == receiver:
            continue
        edges[(taker, receiver)] = edges.get((taker, receiver), 0) + 1
        node_count[taker] = node_count.get(taker, 0) + 1
        node_count[receiver] = node_count.get(receiver, 0) + 1

    edges = {pair: w for pair, w in edges.items() if w >= min_weight}
    if not edges:
        raise ValueError(
            "No repeated delivery combinations found -- try lowering min_weight "
            "or a different set_piece_type."
        )
    node_count = {p: c for p, c in node_count.items() if any(p in pair for pair in edges)}

    players = list(node_count.keys())
    n = len(players)
    angles = {p: 2 * np.pi * i / n for i, p in enumerate(players)}
    pos = {p: (np.cos(a), np.sin(a)) for p, a in angles.items()}

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 7.5))

    max_edge = max(edges.values())
    for (taker, receiver), w in edges.items():
        x0, y0 = pos[taker]
        x1, y1 = pos[receiver]
        ax.plot(
            [x0, x1], [y0, y1], color=pal.accent, alpha=0.35 + 0.55 * (w / max_edge),
            linewidth=1 + 5 * (w / max_edge), zorder=2, solid_capstyle="round",
        )

    max_node = max(node_count.values())
    for p, (x, y) in pos.items():
        size = 260 + 900 * (node_count[p] / max_node)
        ax.scatter(x, y, s=size, color=pal.team_colors[0], edgecolors=pal.ink_primary, linewidths=1.2, zorder=3)
        lx, ly = x * 1.22, y * 1.22
        ax.annotate(
            p, (x, y), xytext=(lx, ly), ha="center", va="center", color=pal.ink_primary,
            fontsize=9, fontweight="bold", zorder=4,
        )

    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(pal.surface)
    if title is None:
        title = f"{set_piece_type.replace('_', ' ').title()} combination network"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax


def plot_metric_histogram(
    values,
    bins: int = 12,
    value_label: str = "value",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    show_stats: bool = True,
    ax=None,
):
    """Classic binned histogram of any continuous metric -- delivery
    distance, added value, time to first contact, whatever's handed in.

    The simplest possible answer to "what's the distribution of this
    number," included because every other distribution chart in this
    module (:func:`plot_value_distribution`'s violins,
    :func:`plot_value_ridgeline`'s KDE curves) is a smoothed estimate --
    sometimes the raw bin counts, with no smoothing assumption baked in,
    are what's actually wanted.

    Args:
        values: any 1-D sequence of numbers (a Series, array, or list).
        value_label: axis label and stat-strip caption for what
            ``values`` represents.
    """
    import matplotlib.pyplot as plt

    pal = theme.get_palette(dark)
    vals = pd.Series(values).dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        raise ValueError("No non-null values to plot.")

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.hist(vals, bins=bins, color=pal.categorical[0], edgecolor=pal.surface, linewidth=1, zorder=3)
    mean_val = float(np.mean(vals))
    ax.axvline(mean_val, color=pal.gold, linewidth=1.5, linestyle="--", zorder=4, label=f"mean = {mean_val:.3g}")
    ax.set_xlabel(value_label)
    ax.set_ylabel("count")
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    pal.style_legend(ax, loc="upper right")
    _style_chart_axis(pal, ax)
    header_stats = None
    if show_stats:
        header_stats = [(str(len(vals)), "events"), (f"{mean_val:.3g}", f"mean {value_label}")]
    if title is None:
        title = f"Distribution of {value_label}"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author, stats=header_stats)
    return fig, ax


def plot_value_boxplot(
    events: pd.DataFrame,
    model,
    set_piece_types: tuple[str, ...] = ("corner", "free_kick"),
    value_col: str = "added_value",
    title: str | None = None,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    footer: str | None = None,
    author: str | None = None,
    dark: bool = True,
    ax=None,
):
    """Box plot of per-delivery added value, one box per set-piece type.

    Exact quartiles, median, and outlier points -- where
    :func:`plot_value_distribution`'s violins show the smoothed *shape*
    of the same data and :func:`plot_value_ridgeline`'s KDE curves show
    it again a third way. Reach for this one when the specific numbers
    (median, IQR, which points are outliers) matter more than the
    overall shape.
    """
    import matplotlib.pyplot as plt

    from ..core.value import set_piece_added_value as _added_value

    pal = theme.get_palette(dark)
    data, labels = [], []
    for t in set_piece_types:
        detail = _added_value(events, t, model)
        vals = detail[value_col].dropna().to_numpy()
        if len(vals) == 0:
            continue
        data.append(vals)
        labels.append(t.replace("_", " "))
    if not data:
        raise ValueError("None of the given set_piece_types has any deliveries to plot.")

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.5))

    bp = ax.boxplot(
        data, patch_artist=True, medianprops=dict(color=pal.surface, linewidth=2),
        whiskerprops=dict(color=pal.ink_secondary), capprops=dict(color=pal.ink_secondary),
        flierprops=dict(markerfacecolor=pal.critical, markeredgecolor=pal.critical, markersize=5, marker="o"),
    )
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(pal.categorical[i % len(pal.categorical)])
        box.set_edgecolor(pal.ink_primary)
        box.set_alpha(0.85)

    ax.set_xticklabels(labels, color=pal.ink_primary)
    ax.axhline(0, color=pal.baseline, linewidth=1, linestyle="--", zorder=1)
    ax.set_ylabel(value_col.replace("_", " "))
    ax.grid(axis="y", color=pal.gridline, linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(pal, ax)
    if title is None:
        title = "Added value by set-piece type"
    _finish_figure(pal, fig, ax, title, subtitle, footer, eyebrow, author)
    return fig, ax
