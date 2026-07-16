"""Shared color palette for :mod:`wa_setpieces.viz`.

Colors are assigned **by the job they do**, per a validated design-system
palette (categorical hues ordered to maximize colorblind-safe separation,
one sequential hue per magnitude scale, a blue/red diverging pair for
signed quantities, and fixed status colors for good/bad outcomes) rather
than picked for looks. The categorical order and hex steps below passed
the standard six-check validator (lightness band, chroma floor, CVD
separation, normal-vision separation, contrast vs. surface) against this
package's dark pitch background.

Do not reorder :data:`CATEGORICAL` or cherry-pick slots out of sequence --
the ordering itself is what keeps adjacent series distinguishable under
color-vision deficiency; a 9th series should fold into "Other" or a facet
rather than extend the list.
"""

from __future__ import annotations

from matplotlib.colors import LinearSegmentedColormap

# Chart chrome (dark surface -- these plots always render on a dark pitch)
SURFACE = "#1a1a19"
PAGE = "#0d0d0d"
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"
PITCH_LINE = "#c7d5cc"

# Categorical palette, fixed order (dark-surface steps). Two-series charts
# (e.g. team A vs. team B) take slots 1-2; never reassign slots per-chart.
CATEGORICAL = [
    "#3987e5",  # 1 blue
    "#008300",  # 2 green
    "#d55181",  # 3 magenta
    "#c98500",  # 4 yellow
    "#199e70",  # 5 aqua
    "#d95926",  # 6 orange
    "#9085e9",  # 7 violet
    "#e66767",  # 8 red
]

# Status colors (fixed -- never reused for series identity)
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"

# Diverging pair for signed quantities (e.g. xT added): blue = positive,
# red = negative, gray = ~zero.
DIVERGING_POSITIVE = CATEGORICAL[0]
DIVERGING_NEGATIVE = "#e66767"
DIVERGING_NEUTRAL = BASELINE

# Sequential blue ramp (light -> dark), the validated default single hue
# for magnitude (heatmap counts, densities).
_SEQUENTIAL_BLUE_STEPS = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]

# Sequential green ramp (light -> dark): the second magnitude hue, for when
# a second sequential scale appears alongside the blue one (e.g. an xT grid
# next to a zone-count heatmap in the same figure) -- interpolated toward
# the validated categorical green, since only the blue ramp ships exact
# steps in the reference palette.
_SEQUENTIAL_GREEN_STEPS = ["#d8f0d8", "#a8dba8", "#6ec06e", "#2fa02f", "#008300", "#005900"]


def sequential_blue_cmap():
    """Single-hue blue colormap, light->dark, for magnitude heatmaps."""
    return LinearSegmentedColormap.from_list("wa_sequential_blue", _SEQUENTIAL_BLUE_STEPS)


def sequential_green_cmap():
    """Single-hue green colormap, light->dark -- pairs with the blue ramp
    when two magnitude scales appear in the same figure."""
    return LinearSegmentedColormap.from_list("wa_sequential_green", _SEQUENTIAL_GREEN_STEPS)


def diverging_cmap():
    """Blue (positive) <-> gray (zero) <-> red (negative) diverging colormap."""
    return LinearSegmentedColormap.from_list(
        "wa_diverging",
        [DIVERGING_NEGATIVE, DIVERGING_NEUTRAL, DIVERGING_POSITIVE],
    )


def style_axis_text(ax, title: str | None = None, fontsize: int = 13) -> None:
    """Apply the shared dark-surface text styling to a pitch/plot axis."""
    if title:
        ax.set_title(title, color=INK_PRIMARY, fontsize=fontsize, pad=10)


def style_legend(ax, **kwargs):
    defaults = dict(facecolor=SURFACE, edgecolor="none", labelcolor=INK_PRIMARY, loc="upper left")
    defaults.update(kwargs)
    return ax.legend(**defaults)
