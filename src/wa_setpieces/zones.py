"""Pitch zones, thirds and channels.

Opta F24 coordinates run 0-100 on both axes and are always expressed in the
*acting team's own attacking direction*: ``x=0`` is that team's own goal
line, ``x=100`` is the opponent's. This holds regardless of which team
touched the ball or which half is being played (verified against
``tests/data/sample_match.json``: every goal sits at x in the high 80s
regardless of team/period, and every clearance sits at low x, near the
clearing team's own goal). ``y`` is pitch width, 0-100 from one touchline to
the other.

Because of this convention, thirds/channels/zones computed here are always
relative to whoever performed the action, not to a fixed pitch side. If you
need to compare or plot events from *both* teams on one shared pitch (e.g.
a corner delivery and the defending team's clearance that followed it), you
must first convert them into a single reference frame with
:func:`to_reference_frame` -- otherwise you're mixing two different
coordinate systems on one plot. This was verified empirically on
``tests/data/sample_match.json`` by pairing each "ball out of play" event
with the throw-in restart it produced (the same physical point on the
touchline, credited to two different teams): mirroring one team's
coordinates with ``x' = 100 - x, y' = 100 - y`` brings the pair to within
~5 pitch units of each other on average, vs. being scattered across the
whole pitch unmirrored.
"""

from __future__ import annotations

import pandas as pd

THIRD_EDGES = (0.0, 100 / 3, 200 / 3, 100.0)
THIRD_LABELS = ("defensive_third", "middle_third", "attacking_third")

# 5-channel split: wide / half-space / central, standard analytics convention.
CHANNEL5_EDGES = (0.0, 100 / 6, 100 / 3, 200 / 3, 500 / 6, 100.0)
CHANNEL5_LABELS = (
    "left_wide",
    "left_half_space",
    "central",
    "right_half_space",
    "right_wide",
)

CHANNEL3_EDGES = (0.0, 100 / 3, 200 / 3, 100.0)
CHANNEL3_LABELS = ("left", "central", "right")


def add_thirds(df: pd.DataFrame, x_col: str = "x", out_col: str = "third") -> pd.DataFrame:
    """Tag each row with its pitch third (defensive/middle/attacking), by ``x``."""
    out = df.copy()
    out[out_col] = pd.cut(
        pd.to_numeric(out[x_col], errors="coerce"),
        bins=THIRD_EDGES,
        labels=THIRD_LABELS,
        include_lowest=True,
    )
    return out


def add_channels(
    df: pd.DataFrame, y_col: str = "y", out_col: str = "channel", n: int = 5
) -> pd.DataFrame:
    """Tag each row with its width channel, by ``y``.

    ``n=5`` (default) gives the standard wide/half-space/central split used
    for crossing and delivery analysis. ``n=3`` gives a coarser left/central/
    right split.
    """
    if n == 5:
        edges, labels = CHANNEL5_EDGES, CHANNEL5_LABELS
    elif n == 3:
        edges, labels = CHANNEL3_EDGES, CHANNEL3_LABELS
    else:
        raise ValueError("n must be 3 or 5")
    out = df.copy()
    out[out_col] = pd.cut(
        pd.to_numeric(out[y_col], errors="coerce"),
        bins=edges,
        labels=labels,
        include_lowest=True,
    )
    return out


def to_reference_frame(
    df: pd.DataFrame,
    reference_team: str,
    team_col: str = "contestantId",
    x_col: str = "x",
    y_col: str = "y",
) -> pd.DataFrame:
    """Convert every row onto one shared pitch frame, anchored on ``reference_team``.

    Rows already belonging to ``reference_team`` are left as-is. Rows from
    the other team are mirrored (``x' = 100 - x``, ``y' = 100 - y``) so that
    every coordinate in the result means the same physical spot on the
    pitch, expressed in ``reference_team``'s own attacking direction. Use
    this before plotting or measuring distances between events from
    different teams (e.g. a delivery and the defender who cleared it).
    """
    out = df.copy()
    mask = out[team_col] != reference_team
    out.loc[mask, x_col] = 100 - pd.to_numeric(out.loc[mask, x_col], errors="coerce")
    out.loc[mask, y_col] = 100 - pd.to_numeric(out.loc[mask, y_col], errors="coerce")
    return out


def zone_id(x: float, y: float, x_bins: int = 6, y_bins: int = 3) -> str | None:
    """Grid cell label ``"R{row}C{col}"`` for a single (x, y) point.

    Row 0 is the widest-``y`` band nearest ``y=0``; col 0 is nearest the
    actor's own goal (``x=0``). Defaults to a 6x3 = 18-zone grid, the
    standard coarse grid used across most public set-piece/possession
    zone models.
    """
    if pd.isna(x) or pd.isna(y):
        return None
    col = min(int(x / 100 * x_bins), x_bins - 1)
    row = min(int(y / 100 * y_bins), y_bins - 1)
    col = max(col, 0)
    row = max(row, 0)
    return f"R{row}C{col}"


def add_zone_grid(
    df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    out_col: str = "zone",
    x_bins: int = 6,
    y_bins: int = 3,
) -> pd.DataFrame:
    """Tag each row with a zone grid cell (see :func:`zone_id`)."""
    out = df.copy()
    x = pd.to_numeric(out[x_col], errors="coerce")
    y = pd.to_numeric(out[y_col], errors="coerce")
    out[out_col] = [
        zone_id(xi, yi, x_bins=x_bins, y_bins=y_bins) for xi, yi in zip(x, y)
    ]
    return out


def zone_counts(
    df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    x_bins: int = 6,
    y_bins: int = 3,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Row counts per zone, optionally split by ``group_cols`` (e.g. team).

    Handy for building a heatmap of where a set piece originates or ends up.
    """
    tagged = add_zone_grid(df, x_col=x_col, y_col=y_col, x_bins=x_bins, y_bins=y_bins)
    keys = (group_cols or []) + ["zone"]
    return tagged.groupby(keys).size().rename("count").reset_index()
