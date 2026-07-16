"""Shared color palette for :mod:`wa_setpieces.viz`, in both a dark and a
light mode.

Colors are assigned **by the job they do** (categorical identity,
sequential/diverging magnitude, fixed status), per a validated
design-system palette, rather than picked for looks. Both the dark and
light categorical steps below -- and the two-color orange/blue
``team_colors`` pairing used for team-vs-team charts -- passed the
standard checks (lightness band, chroma floor, CVD separation,
normal-vision separation, contrast vs. surface) against this module's own
chart surfaces::

    node validate_palette.js "<hex,hex,...>" --mode dark --surface "#0d1117"
    node validate_palette.js "<hex,hex,...>" --mode light --surface "#ffffff"

Do not reorder :data:`CATEGORICAL` (or either mode's ``categorical`` list)
or cherry-pick slots out of sequence -- the ordering itself is what keeps
adjacent series distinguishable under color-vision deficiency; a 9th
series should fold into "Other" or a facet rather than extend the list.
``team_colors`` (orange, then blue) is a separate, deliberately fixed
two-color convention for the exactly-two-teams charts
(:func:`~wa_setpieces.viz.plot_team_comparison` and friends) -- it does
not draw from ``categorical``'s slot order, and was validated on its own
as a standalone pair.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from matplotlib.colors import LinearSegmentedColormap

# Categorical hues: fixed hue order, held constant across both modes --
# only the per-mode lightness step changes (dark surface needs a lighter
# step to hit contrast; light surface needs a darker one).
_CATEGORICAL_DARK = [
    "#3987e5",  # 1 blue
    "#008300",  # 2 green
    "#d55181",  # 3 magenta
    "#c98500",  # 4 yellow
    "#199e70",  # 5 aqua
    "#d95926",  # 6 orange
    "#9085e9",  # 7 violet
    "#e66767",  # 8 red
]
_CATEGORICAL_LIGHT = [
    "#2a78d6",  # 1 blue
    "#008300",  # 2 green
    "#e87ba4",  # 3 magenta
    "#eda100",  # 4 yellow
    "#1baf7a",  # 5 aqua
    "#eb6834",  # 6 orange
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Fixed status/accent colors -- never reused for series identity, never
# themed (same hex in both modes, per the palette's own "status colors are
# fixed" rule).
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"
GOLD = "#c9950f"  # a goal -- distinct from both team colors and status colors

# Sequential blue ramp (light -> dark), the validated default single hue
# for magnitude (heatmap counts, densities). Mode-independent: this is the
# ramp *within* a chart, not the chart's own background.
_SEQUENTIAL_BLUE_STEPS = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]

# Sequential green ramp (light -> dark): the second magnitude hue, for when
# a second sequential scale appears alongside the blue one (e.g. an xT grid
# next to a zone-count heatmap in the same figure).
_SEQUENTIAL_GREEN_STEPS = ["#d8f0d8", "#a8dba8", "#6ec06e", "#2fa02f", "#008300", "#005900"]


@dataclass(frozen=True)
class Palette:
    """One mode's full set of chart colors. Get one via :func:`get_palette`
    rather than constructing directly."""

    dark: bool
    surface: str
    page: str
    ink_primary: str
    ink_secondary: str
    ink_muted: str
    gridline: str
    baseline: str
    pitch_line: str
    categorical: list = field(default_factory=list)
    team_colors: list = field(default_factory=list)
    good: str = GOOD
    critical: str = CRITICAL
    gold: str = GOLD
    # A true neutral gray (R≈G≈B) for the diverging colormap's zero point --
    # deliberately *not* `baseline`, which carries this palette's navy tint
    # for axis/gridline use and would read as "a third hue", not "nothing".
    _diverging_neutral: str = "#383835"

    @property
    def diverging_positive(self) -> str:
        return self.team_colors[1]  # blue

    @property
    def diverging_negative(self) -> str:
        return self.categorical[7]  # red

    @property
    def diverging_neutral(self) -> str:
        return self._diverging_neutral

    def sequential_blue_cmap(self):
        """Single-hue blue colormap, light->dark, for magnitude heatmaps."""
        return LinearSegmentedColormap.from_list("wa_sequential_blue", _SEQUENTIAL_BLUE_STEPS)

    def sequential_green_cmap(self):
        """Single-hue green colormap, light->dark -- pairs with the blue
        ramp when two magnitude scales appear in the same figure."""
        return LinearSegmentedColormap.from_list("wa_sequential_green", _SEQUENTIAL_GREEN_STEPS)

    def diverging_cmap(self):
        """Blue (positive) <-> gray (zero) <-> red (negative) diverging colormap."""
        return LinearSegmentedColormap.from_list(
            "wa_diverging", [self.diverging_negative, self.diverging_neutral, self.diverging_positive]
        )

    def style_axis_text(self, ax, title: str | None = None, subtitle: str | None = None, fontsize: int = 13) -> None:
        """Apply the shared title (bold, primary ink) and optional muted
        subtitle line beneath it -- the "Title" / "date · description"
        two-line header used throughout the gallery."""
        if title:
            ax.set_title(
                title, color=self.ink_primary, fontsize=fontsize, fontweight="bold",
                pad=18 if subtitle else 10,
            )
        if subtitle:
            ax.text(
                0.5, 1.02, subtitle, transform=ax.transAxes, ha="center", va="bottom",
                color=self.ink_secondary, fontsize=max(fontsize * 0.72, 8),
            )

    def style_legend(self, ax, **kwargs):
        defaults = dict(facecolor=self.surface, edgecolor="none", labelcolor=self.ink_primary, loc="upper left")
        defaults.update(kwargs)
        return ax.legend(**defaults)

    def style_footer(self, fig, text: str, fontsize: int = 8) -> None:
        """Small muted credit/source line, bottom-right of the figure --
        opt-in (pass ``footer=...`` to a plotting function); never defaulted,
        since a source credit is specific to whoever is publishing the chart."""
        fig.text(0.99, 0.01, text, ha="right", va="bottom", color=self.ink_muted, fontsize=fontsize)


_DARK = Palette(
    dark=True,
    surface="#0d1117",
    page="#05070c",
    ink_primary="#f2f4f8",
    ink_secondary="#7d8aa3",
    ink_muted="#4d5670",
    gridline="#1b2333",
    baseline="#2a3350",
    pitch_line="#2f3b52",
    categorical=_CATEGORICAL_DARK,
    team_colors=["#d95926", "#3987e5"],  # orange, blue
)

_LIGHT = Palette(
    dark=False,
    surface="#ffffff",
    page="#eef1f6",
    ink_primary="#0b1220",
    ink_secondary="#55607a",
    ink_muted="#8a93aa",
    gridline="#e4e8f0",
    baseline="#c9d0de",
    pitch_line="#c7cedb",
    categorical=_CATEGORICAL_LIGHT,
    team_colors=["#eb6834", "#2a78d6"],  # orange, blue
    _diverging_neutral="#f0efec",
)


def get_palette(dark: bool = True) -> Palette:
    """Return the validated dark or light chart palette.

    Both modes share the same fixed categorical hue order and the same
    orange-then-blue ``team_colors`` convention -- only the per-mode
    lightness step and chart chrome (surface, ink, gridlines) change.
    Every plotting function in :mod:`wa_setpieces.viz` takes a ``dark:
    bool = True`` argument that resolves through this function, so a
    whole figure switches mode with one argument.
    """
    return _DARK if dark else _LIGHT


# --- Backwards-compatible module-level constants (pre-0.7.0 API), pinned
# to the dark palette -- the package's only mode before light/dark support.
# New code should use `get_palette(dark=...)` instead so it can render both.
SURFACE = _DARK.surface
PAGE = _DARK.page
INK_PRIMARY = _DARK.ink_primary
INK_SECONDARY = _DARK.ink_secondary
INK_MUTED = _DARK.ink_muted
GRIDLINE = _DARK.gridline
BASELINE = _DARK.baseline
PITCH_LINE = _DARK.pitch_line
CATEGORICAL = _DARK.categorical
DIVERGING_POSITIVE = _DARK.diverging_positive
DIVERGING_NEGATIVE = _DARK.diverging_negative
DIVERGING_NEUTRAL = _DARK.diverging_neutral


def sequential_blue_cmap():
    """Single-hue blue colormap, light->dark, for magnitude heatmaps."""
    return _DARK.sequential_blue_cmap()


def sequential_green_cmap():
    """Single-hue green colormap, light->dark -- pairs with the blue ramp
    when two magnitude scales appear in the same figure."""
    return _DARK.sequential_green_cmap()


def diverging_cmap():
    """Blue (positive) <-> gray (zero) <-> red (negative) diverging colormap."""
    return _DARK.diverging_cmap()


def style_axis_text(ax, title: str | None = None, subtitle: str | None = None, fontsize: int = 13) -> None:
    """Apply the shared dark-surface text styling to a pitch/plot axis."""
    _DARK.style_axis_text(ax, title, subtitle, fontsize)


def style_legend(ax, **kwargs):
    return _DARK.style_legend(ax, **kwargs)
