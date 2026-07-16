"""Pitch visualizations for set-piece data, built on `mplsoccer
<https://mplsoccer.readthedocs.io>`_.

Every plotting function here takes the same DataFrames the rest of the
package produces (:func:`~opta_setpieces.delivery_locations`,
:func:`~opta_setpieces.zones.zone_counts`, an :class:`~opta_setpieces.XTModel`
grid, ...) and returns the ``(fig, ax)`` matplotlib pair, so you can keep
customizing the plot afterwards.

Requires the optional ``viz`` extra: ``pip install "opta-setpieces[viz]"``.
Opta F24 coordinates (0-100 both axes, each event already in the acting
team's own attacking direction -- see :mod:`opta_setpieces.zones`) map
directly onto :class:`mplsoccer.Pitch`'s built-in ``pitch_type="opta"``, so
no coordinate conversion is needed.
"""

from __future__ import annotations

import pandas as pd

try:
    from mplsoccer import Pitch
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "opta_setpieces.viz requires the 'viz' extra: pip install \"opta-setpieces[viz]\""
    ) from exc

PITCH_COLOR = "#0e1117"
LINE_COLOR = "#c7d5cc"
SUCCESS_COLOR = "#4c9a5b"
FAIL_COLOR = "#c0392b"


def _new_pitch(pitch_type: str = "opta", **pitch_kwargs) -> Pitch:
    kwargs = dict(pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5)
    kwargs.update(pitch_kwargs)
    return Pitch(pitch_type=pitch_type, **kwargs)


def plot_delivery_map(
    deliveries: pd.DataFrame,
    title: str | None = None,
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Arrow map of set-piece deliveries, from :func:`~opta_setpieces.delivery_locations`.

    Successful deliveries (``outcome == 1``) are drawn in green, unsuccessful
    ones in red.

    Returns:
        ``(fig, ax)``. ``fig`` is ``None`` if an existing ``ax`` was passed in.
    """
    pitch = _new_pitch(**(pitch_kwargs or {}))
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=(8, 5.2))
    else:
        pitch.draw(ax=ax)

    success = deliveries[deliveries["outcome"] == 1]
    fail = deliveries[deliveries["outcome"] != 1]

    if not fail.empty:
        pitch.arrows(
            fail["x"], fail["y"], fail["end_x"], fail["end_y"],
            ax=ax, color=FAIL_COLOR, width=2, headwidth=6, alpha=0.85, label="Unsuccessful",
        )
    if not success.empty:
        pitch.arrows(
            success["x"], success["y"], success["end_x"], success["end_y"],
            ax=ax, color=SUCCESS_COLOR, width=2, headwidth=6, alpha=0.9, label="Successful",
        )

    ax.legend(facecolor=PITCH_COLOR, edgecolor="none", labelcolor="white", loc="upper left")
    if title:
        ax.set_title(title, color="white", fontsize=13, pad=10)
    if fig is not None:
        fig.patch.set_facecolor(PITCH_COLOR)
    return fig, ax


def plot_zone_heatmap(
    events: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    x_bins: int = 6,
    y_bins: int = 3,
    title: str | None = None,
    cmap: str = "Reds",
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Zone heatmap (see :mod:`opta_setpieces.zones`) of event counts.

    Any events DataFrame works -- pass a filtered/extracted set (e.g.
    :func:`~opta_setpieces.extract_corners`) to see where a specific
    set-piece type happens most often.
    """
    pitch = _new_pitch(**(pitch_kwargs or {}))
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=(8, 5.2))
    else:
        pitch.draw(ax=ax)

    x = pd.to_numeric(events[x_col], errors="coerce")
    y = pd.to_numeric(events[y_col], errors="coerce")
    valid = x.notna() & y.notna()
    import matplotlib.patheffects as path_effects

    stats = pitch.bin_statistic(x[valid], y[valid], statistic="count", bins=(x_bins, y_bins))
    pitch.heatmap(stats, ax=ax, cmap=cmap, edgecolor=PITCH_COLOR)
    labels = pitch.label_heatmap(
        stats, ax=ax, str_format="{:.0f}", color="white", fontsize=11, ha="center", va="center"
    )
    for label in labels:
        label.set_path_effects(
            [path_effects.Stroke(linewidth=2.5, foreground="black"), path_effects.Normal()]
        )
    if title:
        ax.set_title(title, color="white", fontsize=13, pad=10)
    if fig is not None:
        fig.patch.set_facecolor(PITCH_COLOR)
    return fig, ax


def plot_xt_grid(
    model,
    title: str | None = "Expected Threat (xT) grid",
    cmap: str = "inferno",
    ax=None,
    pitch_kwargs: dict | None = None,
):
    """Heatmap of a fitted :class:`~opta_setpieces.XTModel` grid.

    Darker/brighter cells (per ``cmap``) are worth more xT -- should climb
    steadily towards the opponent's goal (``x=100``) if the fit is sane.
    """
    pitch = _new_pitch(**(pitch_kwargs or {}))
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=(8, 5.2))
    else:
        pitch.draw(ax=ax)

    stats = pitch.bin_statistic(
        [50.0], [50.0], statistic="count", bins=(model.x_bins, model.y_bins)
    )
    stats["statistic"] = model.grid
    pitch.heatmap(stats, ax=ax, cmap=cmap, edgecolor=PITCH_COLOR)
    if title:
        ax.set_title(title, color="white", fontsize=13, pad=10)
    if fig is not None:
        fig.patch.set_facecolor(PITCH_COLOR)
    return fig, ax


def plot_second_phase(
    events: pd.DataFrame,
    delivery_event_id: int,
    title: str | None = None,
    ax=None,
    pitch_kwargs: dict | None = None,
    **phase_kwargs,
):
    """Visualize one corner/free-kick's delivery and its phase-window events.

    Draws the delivery as a solid arrow, then each subsequent touch in the
    phase window as a numbered, faded marker so you can follow the passage
    of play. The second-phase shot (if any) is highlighted.

    Args:
        delivery_event_id: the ``eventId`` of a corner or free-kick delivery
            (as returned by :func:`~opta_setpieces.extract_corners` /
            :func:`~opta_setpieces.extract_free_kicks`).
        **phase_kwargs: forwarded to :func:`opta_setpieces.phases.classify_phase`
            (e.g. ``clear_safe_x``, ``max_gap_seconds``).
    """
    from .phases import _phase_window, _seconds, classify_phase
    from .zones import to_reference_frame

    delivery_row = events.loc[events["eventId"] == delivery_event_id].iloc[0]
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

    pitch = _new_pitch(**(pitch_kwargs or {}))
    fig = None
    if ax is None:
        fig, ax = pitch.draw(figsize=(8, 5.2))
    else:
        pitch.draw(ax=ax)

    pitch.arrows(
        [delivery_row["x"]], [delivery_row["y"]],
        [window.iloc[0]["x"]] if not window.empty else [delivery_row["x"]],
        [window.iloc[0]["y"]] if not window.empty else [delivery_row["y"]],
        ax=ax, color="white", width=2.5, headwidth=7, label="Delivery",
    )

    for i, (_, row) in enumerate(window.iterrows()):
        is_second_phase_shot = row["eventId"] == result.second_phase_event_id
        color = "#f1c40f" if is_second_phase_shot else "#7f8c8d"
        size = 260 if is_second_phase_shot else 140
        pitch.scatter(row["x"], row["y"], ax=ax, color=color, s=size, edgecolors="white", zorder=3)
        ax.annotate(
            str(i + 1), (row["x"], row["y"]), color="black", fontsize=8,
            ha="center", va="center", zorder=4,
        )

    ax.legend(facecolor=PITCH_COLOR, edgecolor="none", labelcolor="white", loc="upper left")
    if title is None:
        outcome = (
            "second-phase shot" if result.second_phase_shot
            else "cleared" if result.cleared_immediately
            else "no clear resolution"
        )
        title = f"{result.set_piece_type or 'set piece'} — eventId {delivery_event_id} ({outcome})"
    ax.set_title(title, color="white", fontsize=12, pad=10)
    if fig is not None:
        fig.patch.set_facecolor(PITCH_COLOR)
    return fig, ax
