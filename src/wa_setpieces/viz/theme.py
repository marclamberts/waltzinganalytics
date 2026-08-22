"""Shared color palette for :mod:`wa_setpieces.viz`, in both a dark and a
light mode -- the Waltzing Analytics house style, in both of its two
canvases.

Colors are assigned **by the job they do** (categorical identity,
sequential/diverging magnitude, fixed status), not picked for looks.
Every anchor color below -- canvas, ink, muted tones, the hairline, the
single coral accent, the team-1/team-2 pairing, and four of each mode's
eight categorical hues -- is sampled directly from Waltzing Analytics'
own delivered chart/report work (dark navy/coral presentation reports;
light "paper" scouting exports), not invented for this module. The
remaining categorical slots needed to cover eight distinct series (this
package's routine taxonomies, zone breakdowns, etc. regularly need more
than WA's four documented per-mode hues) are extended from those same
anchors -- WA's own confidence-tier green/red and brand amber/coral
folded in as additional categorical hues, and one muted slate-blue
derived to round out the set -- rather than reaching for an unrelated
hue family. See each list below for exactly which slots are which.

Do not reorder :data:`CATEGORICAL` (or either mode's ``categorical``
list) or cherry-pick slots out of sequence -- the ordering is what keeps
adjacent series distinguishable, and a 9th series should fold into
"Other" or a facet rather than extend the list further without
re-checking separation. ``team_colors`` is a separate, deliberately
fixed two-color convention for exactly-two-teams charts
(:func:`~wa_setpieces.viz.plot_team_comparison` and friends): teal vs.
blue, the same pairing WA's own dark presentation-report family uses for
team-1/team-2 identity, mirrored into light mode with that family's
light-mode teal-green/blue equivalents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from matplotlib.colors import LinearSegmentedColormap

# Categorical hues: fixed hue order, held constant across both modes --
# only the per-mode lightness/saturation step changes (dark surface needs
# a lighter step to hit contrast; light surface needs a darker one).
#
# Slots 1-4 in each mode are WA's own documented per-mode categorical
# hues, in the order WA uses them. Slots 5-8 extend the set to cover
# eight distinct series, drawing on WA's *other* documented brand hues
# (confidence-tier green/red, brand amber, the single coral accent)
# rather than an unrelated hue family -- see the module docstring.
_CATEGORICAL_DARK = [
    "#5b8ac9",  # 1 blue      -- WA dark neutral-categorical blue
    "#1fa88c",  # 2 teal      -- WA dark team-identity teal, reused generically
    "#b37f1e",  # 3 gold      -- WA dark neutral-categorical gold
    "#e8794c",  # 4 coral     -- WA's single brand accent, promoted to a series color
    "#d9663a",  # 5 orange-red -- WA dark neutral-categorical orange-red
    "#5c6e7e",  # 6 slate     -- lightened from WA's dark "contested" slate #3c4a57
    "#3c9b5c",  # 7 green     -- WA confidence-tier green, dark-surface-safe shade
    "#c9564f",  # 8 red       -- WA confidence-tier red, dark-surface-safe shade
]
_CATEGORICAL_LIGHT = [
    "#2a78d6",  # 1 blue       -- WA light categorical blue
    "#1baf7a",  # 2 teal-green -- WA light categorical teal-green
    "#4a3aa7",  # 3 purple     -- WA light categorical purple
    "#eb6834",  # 4 orange-red -- WA light categorical orange-red
    "#f5a623",  # 5 amber      -- WA's brand amber, promoted to a series color
    "#1faa1f",  # 6 green      -- WA confidence-tier green
    "#d03b3b",  # 7 red        -- WA confidence-tier red
    "#7c8ca6",  # 8 slate-blue -- light-mode extension of the dark "slate" neutral
]

# Fixed status/accent colors -- never reused for series identity, never
# themed (same hex in both modes, per the palette's own "status colors are
# fixed" rule). GOOD/CRITICAL reuse WA's own confidence-tier green/red --
# this package's "good"/"critical" is exactly that same semantic (a
# trust/quality signal), not a fresh color decision.
GOOD = "#1faa1f"
CRITICAL = "#d03b3b"
GOLD = "#eda100"  # a goal -- WA's deeper brand amber, distinct from categorical gold/amber

# Sequential blue ramp (light -> dark), the default single hue for
# magnitude (heatmap counts, densities), interpolated toward WA's own
# dark-mode categorical blue (#5b8ac9). Mode-independent: this is the ramp
# *within* a chart, not the chart's own background.
_SEQUENTIAL_BLUE_STEPS = [
    "#dce9f7", "#d1e1f3", "#c6d9ef", "#bcd1ec", "#b1c9e8",
    "#a6c1e4", "#9cbae0", "#91b2dc", "#86aad8", "#7ba2d4",
    "#709ad1", "#6692cd", "#5b8ac9",
]

# Sequential teal ramp (light -> dark): the second magnitude hue, for when
# a second sequential scale appears alongside the blue one (e.g. an xT grid
# next to a zone-count heatmap in the same figure) -- interpolated toward
# WA's own team-identity teal (#1fa88c).
_SEQUENTIAL_GREEN_STEPS = ["#d6f0ea", "#b1e2d7", "#8dd3c4", "#68c5b2", "#44b69f", "#1fa88c"]


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
    # A true neutral gray (R~=G~=B, only barely warm-tinted to match WA's
    # paper/navy undertone) for the diverging colormap's zero point --
    # deliberately *not* `baseline`, which carries this palette's own hue
    # tint for axis/gridline use and would read as "a third hue", not
    # "nothing".
    _diverging_neutral: str = "#353634"

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
        """Single-hue teal/green colormap, light->dark -- pairs with the
        blue ramp when two magnitude scales appear in the same figure."""
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
    surface="#14202b",   # WA dark navy canvas
    page="#0d151c",      # darker navy, one step behind the canvas
    ink_primary="#f2efe6",   # WA cream title ink
    ink_secondary="#a8a6a0",  # WA muted-2 (subtitle-weight)
    ink_muted="#86847e",      # WA muted (footnote-weight)
    gridline="#283541",   # dimmed toward the canvas from the WA hairline
    baseline="#646f79",   # lightened WA hairline, for axis/zero-line emphasis
    pitch_line="#505c68",  # WA hairline #384653, lightened slightly for pitch outlines
    categorical=_CATEGORICAL_DARK,
    team_colors=["#1fa88c", "#5b8ac9"],  # teal (team 1), blue (team 2) -- WA's own pairing
)

_LIGHT = Palette(
    dark=False,
    surface="#fcfcfb",   # WA paper canvas
    page="#eae8e0",      # warm gray, one step behind the paper
    ink_primary="#15171a",   # WA ink
    ink_secondary="#86847e",  # WA muted (subtitle-weight)
    ink_muted="#a8a6a0",      # WA muted-2 (footnote-weight)
    gridline="#e5e2d8",   # warm light gray, paper-toned
    baseline="#dcd8cb",
    pitch_line="#d8d3c5",
    categorical=_CATEGORICAL_LIGHT,
    team_colors=["#1baf7a", "#2a78d6"],  # teal-green (team 1), blue (team 2)
    _diverging_neutral="#f4f3f0",
)


def get_palette(dark: bool = True) -> Palette:
    """Return the Waltzing Analytics dark or light chart palette.

    Both modes share the same fixed categorical hue order and the same
    teal-then-blue ``team_colors`` convention -- only the per-mode
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
    """Single-hue teal/green colormap, light->dark -- pairs with the blue
    ramp when two magnitude scales appear in the same figure."""
    return _DARK.sequential_green_cmap()


def diverging_cmap():
    """Blue (positive) <-> gray (zero) <-> red (negative) diverging colormap."""
    return _DARK.diverging_cmap()


def style_axis_text(ax, title: str | None = None, subtitle: str | None = None, fontsize: int = 13) -> None:
    """Apply the shared dark-surface text styling to a pitch/plot axis."""
    _DARK.style_axis_text(ax, title, subtitle, fontsize)


def style_legend(ax, **kwargs):
    return _DARK.style_legend(ax, **kwargs)
