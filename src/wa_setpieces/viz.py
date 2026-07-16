"""Pitch and chart visualizations for set-piece data, built on `mplsoccer
<https://mplsoccer.readthedocs.io>`_ and matplotlib.

Every plotting function here takes the same DataFrames the rest of the
package produces (:func:`~wa_setpieces.delivery_locations`,
:func:`~wa_setpieces.zones.zone_counts`, an :class:`~wa_setpieces.XTModel`
grid, ...) and returns the ``(fig, ax)`` matplotlib pair, so you can keep
customizing the plot afterwards.

Requires the optional ``viz`` extra: ``pip install "wa-setpieces[viz]"``.
Opta F24 coordinates (0-100 both axes, each event already in the acting
team's own attacking direction -- see :mod:`wa_setpieces.zones`) map
directly onto :class:`mplsoccer.Pitch`'s built-in ``pitch_type="opta"``, so
no coordinate conversion is needed.

Colors follow :mod:`wa_setpieces.theme` -- assigned by the job they do
(status, category, magnitude, sign), not picked for looks. See that
module's docstring before adding a new plot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from mplsoccer import Pitch
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "wa_setpieces.viz requires the 'viz' extra: pip install \"wa-setpieces[viz]\""
    ) from exc

from . import theme

# Backwards-compatible aliases (pre-theme-module names).
PITCH_COLOR = theme.SURFACE
LINE_COLOR = theme.PITCH_LINE
SUCCESS_COLOR = theme.GOOD
FAIL_COLOR = theme.CRITICAL


def _new_pitch(pitch_type: str = "opta", **pitch_kwargs) -> Pitch:
    kwargs = dict(pitch_color=theme.SURFACE, line_color=theme.PITCH_LINE, linewidth=1.5)
    kwargs.update(pitch_kwargs)
    return Pitch(pitch_type=pitch_type, **kwargs)


def _draw_pitch(ax, pitch_kwargs, figsize=(8, 5.2)):
    pitch = _new_pitch(**(pitch_kwargs or {}))
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=figsize)
    else:
        pitch.draw(ax=ax)
    return pitch, fig, ax


def _style_chart_axis(ax, title: str | None = None):
    ax.set_facecolor(theme.SURFACE)
    for spine in ax.spines.values():
        spine.set_color(theme.GRIDLINE)
    ax.tick_params(colors=theme.INK_SECONDARY)
    ax.xaxis.label.set_color(theme.INK_SECONDARY)
    ax.yaxis.label.set_color(theme.INK_SECONDARY)
    if title:
        ax.set_title(title, color=theme.INK_PRIMARY, fontsize=13, pad=10)


def plot_delivery_map(
    deliveries: pd.DataFrame,
    title: str | None = None,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Arrow map of set-piece deliveries, from :func:`~wa_setpieces.delivery_locations`.

    Successful deliveries (``outcome == 1``) are drawn in the status "good"
    color, unsuccessful ones in "critical" -- outcome is a status, not a
    team identity, so it never borrows the categorical team palette.

    Returns:
        ``(fig, ax)``. ``fig`` is ``None`` if an existing ``ax`` was passed in.
    """
    pitch, fig, ax = _draw_pitch(ax, pitch_kwargs)

    success = deliveries[deliveries["outcome"] == 1]
    fail = deliveries[deliveries["outcome"] != 1]

    if not fail.empty:
        pitch.arrows(
            fail["x"], fail["y"], fail["end_x"], fail["end_y"],
            ax=ax, color=theme.CRITICAL, width=2, headwidth=6, alpha=0.9, label="Unsuccessful",
        )
    if not success.empty:
        pitch.arrows(
            success["x"], success["y"], success["end_x"], success["end_y"],
            ax=ax, color=theme.GOOD, width=2, headwidth=6, alpha=0.95, label="Successful",
        )

    theme.style_legend(ax)
    theme.style_axis_text(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_zone_heatmap(
    events: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    x_bins: int = 6,
    y_bins: int = 3,
    title: str | None = None,
    cmap=None,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Zone heatmap (see :mod:`wa_setpieces.zones`) of event counts.

    Any events DataFrame works -- pass a filtered/extracted set (e.g.
    :func:`~wa_setpieces.extract_corners`) to see where a specific
    set-piece type happens most often. Defaults to the single-hue
    sequential blue ramp (counts are a magnitude, not a category).
    """
    import matplotlib.patheffects as path_effects

    pitch, fig, ax = _draw_pitch(ax, pitch_kwargs)
    cmap = cmap if cmap is not None else theme.sequential_blue_cmap()

    x = pd.to_numeric(events[x_col], errors="coerce")
    y = pd.to_numeric(events[y_col], errors="coerce")
    valid = x.notna() & y.notna()

    stats = pitch.bin_statistic(x[valid], y[valid], statistic="count", bins=(x_bins, y_bins))
    pitch.heatmap(stats, ax=ax, cmap=cmap, edgecolor=theme.SURFACE)
    labels = pitch.label_heatmap(
        stats, ax=ax, str_format="{:.0f}", color=theme.INK_PRIMARY, fontsize=11,
        ha="center", va="center",
    )
    for label in labels:
        label.set_path_effects(
            [path_effects.Stroke(linewidth=2.5, foreground="black"), path_effects.Normal()]
        )
    theme.style_axis_text(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_xt_grid(
    model,
    title: str | None = "Expected Threat (xT) grid",
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
    pitch, fig, ax = _draw_pitch(ax, pitch_kwargs)
    cmap = cmap if cmap is not None else theme.sequential_green_cmap()

    stats = pitch.bin_statistic(
        [50.0], [50.0], statistic="count", bins=(model.x_bins, model.y_bins)
    )
    stats["statistic"] = model.grid
    pitch.heatmap(stats, ax=ax, cmap=cmap, edgecolor=theme.SURFACE)
    theme.style_axis_text(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_second_phase(
    events: pd.DataFrame,
    delivery_event_id: int,
    contestant_id: str | None = None,
    title: str | None = None,
    ax=None,
    pitch_kwargs: dict | None = None,
    **phase_kwargs,
):
    """Visualize one corner/free-kick's delivery and its phase-window events.

    Draws the delivery as a solid arrow, then each subsequent touch in the
    phase window as a numbered, faded marker so you can follow the passage
    of play. The second-phase shot (if any) is highlighted in the
    categorical yellow slot (a specific touch to pick out, not a status).

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
        **phase_kwargs: forwarded to :func:`wa_setpieces.phases.classify_phase`
            (e.g. ``clear_safe_x``, ``max_gap_seconds``).
    """
    from .filters import extract_corners, extract_free_kicks
    from .phases import _phase_window, _seconds, classify_phase
    from .zones import to_reference_frame

    candidates = pd.concat([extract_corners(events), extract_free_kicks(events)])
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
            f"deliveries (eventId is only unique per team in F24) -- pass "
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

    pitch, fig, ax = _draw_pitch(ax, pitch_kwargs)

    pitch.arrows(
        [delivery_row["x"]], [delivery_row["y"]],
        [window.iloc[0]["x"]] if not window.empty else [delivery_row["x"]],
        [window.iloc[0]["y"]] if not window.empty else [delivery_row["y"]],
        ax=ax, color=theme.INK_PRIMARY, width=2.5, headwidth=7, label="Delivery",
    )

    highlight = theme.CATEGORICAL[3]  # yellow -- picking out one touch, not a status/team
    for i, (_, row) in enumerate(window.iterrows()):
        is_second_phase_shot = row["eventId"] == result.second_phase_event_id
        color = highlight if is_second_phase_shot else theme.INK_MUTED
        size = 260 if is_second_phase_shot else 140
        pitch.scatter(
            row["x"], row["y"], ax=ax, color=color, s=size,
            edgecolors=theme.INK_PRIMARY, zorder=3,
        )
        ax.annotate(
            str(i + 1), (row["x"], row["y"]), color="black", fontsize=8,
            ha="center", va="center", zorder=4,
        )

    theme.style_legend(ax)
    if title is None:
        outcome = (
            "second-phase shot" if result.second_phase_shot
            else "cleared" if result.cleared_immediately
            else "no clear resolution"
        )
        title = f"{result.set_piece_type or 'set piece'} — eventId {delivery_event_id} ({outcome})"
    theme.style_axis_text(ax, title, fontsize=12)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_team_comparison(
    summary: pd.DataFrame,
    metric: str = "attempts",
    team_names: dict | None = None,
    team_order: list | None = None,
    title: str | None = None,
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
            the first (blue) categorical slot -- otherwise it falls out of
            row order in ``summary``, which isn't meaningful. Pass this
            whenever "our team" should consistently be the same color
            across a set of charts (see :func:`plot_dashboard`).

    Returns:
        ``(fig, ax)``.
    """
    import matplotlib.pyplot as plt

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

    for i, team in enumerate(teams):
        team_rows = summary[summary["contestantId"] == team].set_index("set_piece_type")
        values = [team_rows[metric].get(t, 0) for t in types]
        offset = (i - (len(teams) - 1) / 2) * bar_height
        label = (team_names or {}).get(team, f"{team[:8]}…")
        ax.barh(
            y + offset, values, height=bar_height * 0.92,
            color=theme.CATEGORICAL[i], label=label,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([t.replace("_", " ") for t in types], color=theme.INK_PRIMARY)
    ax.set_xlabel(metric.replace("_", " "))
    ax.invert_yaxis()
    ax.grid(axis="x", color=theme.GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    theme.style_legend(ax, loc="lower right")
    _style_chart_axis(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_xt_added_bars(
    delivery_xt: pd.DataFrame,
    value_col: str = "xt_added",
    label_col: str = "playerName",
    top_n: int = 15,
    title: str | None = "xT added per delivery",
    ax=None,
):
    """Diverging bar chart of a signed per-delivery value (positive vs. negative).

    Works for either :func:`~wa_setpieces.xt.set_piece_delivery_xt`'s
    ``xt_added`` (the default) or :func:`~wa_setpieces.value.set_piece_added_value`'s
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

    valid = delivery_xt.dropna(subset=[value_col]).copy()
    valid = valid.reindex(valid[value_col].abs().sort_values(ascending=False).index)
    valid = valid.head(top_n).sort_values(value_col)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 0.4 * len(valid) + 1.5))

    colors = [theme.DIVERGING_POSITIVE if v >= 0 else theme.DIVERGING_NEGATIVE
              for v in valid[value_col]]
    y = np.arange(len(valid))
    ax.barh(y, valid[value_col], color=colors)
    ax.axvline(0, color=theme.BASELINE, linewidth=1)
    labels = valid[label_col].fillna(valid["eventId"].astype(str)) if label_col in valid else valid["eventId"]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=theme.INK_PRIMARY, fontsize=9)
    ax.set_xlabel(value_col.replace("_", " "))
    ax.grid(axis="x", color=theme.GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    _style_chart_axis(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_corner_sonar(
    deliveries: pd.DataFrame,
    title: str | None = "Corner sonar",
    ax=None,
):
    """Polar "sonar" plot of corner (or free-kick) delivery angle and distance.

    Each delivery is one point: angle is the direction from the restart spot
    to where the ball ended up, radius is how far it travelled. Colored by
    outcome (status, not team) exactly like :func:`plot_delivery_map`, so
    the two read consistently together.

    Requires a polar ``ax`` if you pass one in
    (``plt.subplots(subplot_kw={"projection": "polar"})``).
    """
    import matplotlib.pyplot as plt

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    d = deliveries.dropna(subset=["end_x", "end_y"]).copy()
    dx = d["end_x"] - d["x"]
    dy = d["end_y"] - d["y"]
    angle = np.arctan2(dy, dx)
    radius = np.hypot(dx, dy)
    colors = np.where(d["outcome"] == 1, theme.GOOD, theme.CRITICAL)

    ax.scatter(angle, radius, c=colors, s=90, edgecolors=theme.INK_PRIMARY, linewidths=0.8, zorder=3)
    ax.set_facecolor(theme.SURFACE)
    ax.set_theta_zero_location("E")
    ax.tick_params(colors=theme.INK_SECONDARY)
    ax.spines["polar"].set_color(theme.GRIDLINE)
    ax.grid(color=theme.GRIDLINE)
    theme.style_axis_text(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_match_timeline(
    events: pd.DataFrame,
    team_names: dict | None = None,
    title: str | None = "Set pieces through the match",
    ax=None,
):
    """Swim-lane timeline of every set piece across the match.

    One row per set-piece type, one marker per delivery, positioned by
    match minute. Opta's ``timeMin`` already runs cumulatively across
    periods (period 2 starts at ~45, not 0 -- verified against
    ``tests/data/sample_match.json``, where period 1 spans timeMin 0-51 and
    period 2 spans 45-96), so it's used as-is with no per-period offset.
    Colored by team (a 2-category comparison, the safe end of the
    validated categorical order) -- the set-piece *type* is already
    encoded by row, so it doesn't need its own color too.
    """
    import matplotlib.pyplot as plt

    from .constants import SET_PIECE_TYPES
    from .filters import tag_set_pieces

    tagged = tag_set_pieces(events)
    sp = tagged[tagged["set_piece_type"].notna()].copy()
    sp["match_minute"] = pd.to_numeric(sp["timeMin"], errors="coerce")

    types = [t for t in SET_PIECE_TYPES if t in set(sp["set_piece_type"])]
    type_pos = {t: i for i, t in enumerate(types)}
    teams = list(sp["contestantId"].drop_duplicates())[:2]
    team_color = {team: theme.CATEGORICAL[i] for i, team in enumerate(teams)}

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 0.6 * len(types) + 1.5))

    for team in teams:
        team_rows = sp[sp["contestantId"] == team]
        y = team_rows["set_piece_type"].map(type_pos)
        label = (team_names or {}).get(team, f"{team[:8]}…")
        ax.scatter(
            team_rows["match_minute"], y, color=team_color[team], s=70,
            edgecolors=theme.INK_PRIMARY, linewidths=0.6, label=label, zorder=3,
        )

    for i in type_pos.values():
        ax.axhline(i, color=theme.GRIDLINE, linewidth=0.8, zorder=1)
    ax.axvline(45, color=theme.BASELINE, linewidth=1, linestyle="--", zorder=1, label="Half-time")

    ax.set_yticks(list(type_pos.values()))
    ax.set_yticklabels([t.replace("_", " ") for t in types], color=theme.INK_PRIMARY)
    ax.set_xlabel("Match minute")
    ax.invert_yaxis()
    theme.style_legend(ax, loc="upper right", ncol=1)
    _style_chart_axis(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax


def plot_dashboard(
    events: pd.DataFrame,
    team_id: str,
    set_piece_type: str = "corner",
    team_names: dict | None = None,
    title: str | None = None,
):
    """One-figure set-piece report card for a team: delivery map, end-zone
    heatmap, and attempts/success-rate comparison against their opponent.

    Combines :func:`plot_delivery_map`, :func:`plot_zone_heatmap` and
    :func:`plot_team_comparison` into a single figure with
    :class:`matplotlib.gridspec.GridSpec`, in the spirit of a scouting
    report -- this is the "hero" figure to reach for over the individual
    plots when you want one shareable image.

    Returns:
        ``fig`` (a new figure; there's no single ``ax`` to hand back).
    """
    import matplotlib.pyplot as plt

    from .metrics import delivery_locations, set_piece_summary

    fig = plt.figure(figsize=(13, 9), facecolor=theme.SURFACE)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=0.35, wspace=0.25)

    deliveries = delivery_locations(events, set_piece_type)
    team_deliveries = deliveries[deliveries["contestantId"] == team_id]
    label = (team_names or {}).get(team_id, f"{team_id[:8]}…")

    ax_map = fig.add_subplot(gs[0, 0])
    plot_delivery_map(team_deliveries, title=f"{label} — {set_piece_type} deliveries", ax=ax_map)

    ax_heat = fig.add_subplot(gs[0, 1])
    plot_zone_heatmap(
        team_deliveries, x_col="end_x", y_col="end_y",
        title=f"{label} — {set_piece_type} end zones", ax=ax_heat,
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
        title="Attempts by set-piece type", ax=ax_attempts,
    )

    ax_rate = fig.add_subplot(gs[1, 1])
    plot_team_comparison(
        both_teams, metric="success_rate", team_names=team_names, team_order=team_order,
        title="Success rate by set-piece type", ax=ax_rate,
    )

    fig.suptitle(title or f"{label} — set-piece report", color=theme.INK_PRIMARY, fontsize=16, y=0.98)
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
        fig, ax = radar.setup_axis(facecolor=theme.SURFACE, figsize=(9, 9))
    else:
        radar.setup_axis(facecolor=theme.SURFACE, ax=ax)

    radar.draw_circles(ax=ax, facecolor=theme.SURFACE, edgecolor=theme.GRIDLINE)
    radar.draw_radar_compare(
        values_a, values_b, ax=ax,
        kwargs_radar={"facecolor": theme.CATEGORICAL[0], "alpha": 0.6},
        kwargs_compare={"facecolor": theme.CATEGORICAL[1], "alpha": 0.6},
    )
    radar.draw_range_labels(ax=ax, color=theme.INK_SECONDARY, fontsize=9)
    radar.draw_param_labels(ax=ax, color=theme.INK_PRIMARY, fontsize=11)

    import matplotlib.patches as mpatches

    label_a = (team_names or {}).get(row_a["contestantId"], f"{row_a['contestantId'][:8]}…")
    label_b = (team_names or {}).get(row_b["contestantId"], f"{row_b['contestantId'][:8]}…")
    handles = [
        mpatches.Patch(color=theme.CATEGORICAL[0], label=label_a),
        mpatches.Patch(color=theme.CATEGORICAL[1], label=label_b),
    ]
    # loc="upper right" with no bbox_to_anchor keeps the legend inside the
    # axes' own bounding box (radar param labels leave the corners empty) --
    # placing it outside via bbox_to_anchor got silently clipped by any
    # savefig call that doesn't pass bbox_inches="tight" (e.g. sphinx-gallery's
    # default scraper), losing the text entirely.
    ax.legend(
        handles=handles, loc="upper right",
        facecolor=theme.SURFACE, edgecolor="none", labelcolor=theme.INK_PRIMARY,
    )
    theme.style_axis_text(ax, title)
    if fig is not None:
        fig.patch.set_facecolor(theme.SURFACE)
    return fig, ax
