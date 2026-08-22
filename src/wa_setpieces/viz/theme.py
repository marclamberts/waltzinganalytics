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
from datetime import date

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

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

# Sequential ramps for magnitude (heatmap counts, densities) -- mode-aware,
# unlike the categorical/status colors above: a low value should read as
# "barely there" against *this mode's own canvas*, a high value as the full
# saturated hue. A fixed light->dark ramp (pale pastel at the low end) looks
# right on white paper but reads as a disconnected, pasted-in light-mode
# widget on the dark navy canvas -- confirmed by rendering a zone heatmap in
# dark mode with the old fixed ramp: the pale blue cells looked like a
# different app's output next to the WA-branded header above them. So the
# low end blends toward *this palette's own surface color* instead of a
# fixed pale hue, and only the high end (the saturated target hue) is fixed
# across both modes.
_SEQUENTIAL_BLUE_TARGET = "#5b8ac9"    # WA's own categorical blue, both modes' high end
_SEQUENTIAL_GREEN_TARGET = "#1fa88c"   # WA's own team-identity teal, both modes' high end


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    a = tuple(int(hex_a.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    b = tuple(int(hex_b.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    rgb = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def _ramp(low: str, high: str, n: int) -> list[str]:
    return [_mix(low, high, i / (n - 1)) for i in range(n)]


def _truncate_to_width(fig, renderer, text: str, prop, max_width_px: float) -> str:
    """Truncate ``text`` with a trailing "…" so it renders no wider than
    ``max_width_px`` under ``prop`` (a :class:`~matplotlib.font_manager.FontProperties`).
    Binary search over candidate lengths, reusing one already-drawn
    ``renderer`` to measure each candidate (``get_text_width_height_descent``
    needs no further canvas redraw) -- this is what keeps a long title from
    running into the WA lockup on a narrow figure instead of overlapping it.
    """
    w, _, _ = renderer.get_text_width_height_descent(text, prop, False)
    if w <= max_width_px:
        return text
    lo, hi = 1, len(text)
    best = "…"
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid].rstrip() + "…"
        w, _, _ = renderer.get_text_width_height_descent(candidate, prop, False)
        if w <= max_width_px:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best


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
    # WA's single brand accent -- the eyebrow bullet+label, the WA lockup
    # mark, headline callouts. Coral in dark mode, amber in light mode,
    # per WA's own two canvases (see the module docstring).
    accent: str = "#e8794c"
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
        """Single-hue blue colormap for magnitude heatmaps -- low values
        blend toward this mode's own canvas color, high values are WA's
        saturated categorical blue, so the ramp reads as part of the same
        card in both dark and light mode rather than a fixed light-mode
        pastel pasted onto a dark canvas."""
        low = _mix(self.surface, _SEQUENTIAL_BLUE_TARGET, 0.22 if self.dark else 0.19)
        return LinearSegmentedColormap.from_list("wa_sequential_blue", _ramp(low, _SEQUENTIAL_BLUE_TARGET, 13))

    def sequential_green_cmap(self):
        """Single-hue teal/green colormap, same low-blends-toward-canvas
        logic as :meth:`sequential_blue_cmap` -- pairs with the blue ramp
        when two magnitude scales appear in the same figure."""
        low = _mix(self.surface, _SEQUENTIAL_GREEN_TARGET, 0.22 if self.dark else 0.19)
        return LinearSegmentedColormap.from_list("wa_sequential_green", _ramp(low, _SEQUENTIAL_GREEN_TARGET, 13))

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

    def draw_eyebrow(self, fig, text: str, x_in: float = 0.28, y_in: float = 0.24, fontsize: float = 9.5) -> None:
        """Small square bullet + all-caps label, top-left of the figure --
        the category/context line above the title (e.g. "CORNER · TREND
        NOTE"). A unicode square glyph inline with the text, colored with
        it, rather than a separate patch -- simpler to position and just
        as legible."""
        fig_w, fig_h = fig.get_size_inches()
        fig.text(
            x_in / fig_w, 1 - y_in / fig_h, f"■  {text.upper()}",
            transform=fig.transFigure, ha="left", va="top",
            color=self.accent, fontsize=fontsize, fontweight="bold",
        )

    def draw_wa_lockup(self, fig, author: str | None = None, x_in: float = 0.28, y_in: float = 0.24) -> float:
        """The package's own brand lockup -- a bold "WA" mark, a divider,
        and the "WALTZING ANALYTICS" wordmark (+ an optional byline line
        if ``author`` is given) -- top-right of the figure. This is WA's
        own brand identity, not the caller's: pass ``author=`` to add a
        personal byline underneath the wordmark, but there's no default
        byline -- everyone who uses this package gets the same WA mark,
        not a name that isn't theirs.

        The divider and "WA" mark are positioned from the wordmark's
        *measured* rendered width (a forced ``fig.canvas.draw()`` plus
        ``get_window_extent``), not a guessed inch offset -- bold text at
        small point sizes is reliably wider than eyeballed estimates, and
        a guessed offset ends up drawing the divider through the text
        instead of beside it.

        Returns:
            The lockup's own leftmost x position, in figure-fraction
            coordinates -- :meth:`draw_header` uses this to keep the title
            from running into it on a narrow figure.
        """
        fig_w, fig_h = fig.get_size_inches()
        right_x = 1 - x_in / fig_w
        top_y = 1 - y_in / fig_h

        wordmark = fig.text(
            right_x, top_y, "WALTZING ANALYTICS", transform=fig.transFigure,
            ha="right", va="top", color=self.ink_primary, fontsize=8.5, fontweight="bold",
        )
        byline = None
        if author:
            byline = fig.text(
                right_x, top_y, author.upper(), transform=fig.transFigure,
                ha="right", va="top", color=self.ink_muted, fontsize=7,
            )

        # First pass: render once so each line's real height is known, then
        # restack them top-to-bottom with a small fixed gap (their initial
        # positions overlap -- only used to measure, not to place).
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        lines = [wordmark] + ([byline] if byline else [])
        heights_px = [t.get_window_extent(renderer=renderer).height for t in lines]

        gap_px = 3
        y_px = top_y * fig.bbox.height
        for text_obj, h_px in zip(lines, heights_px):
            text_obj.set_position((right_x, y_px / fig.bbox.height))
            y_px -= h_px + gap_px

        # Second pass: positions above are final -- measure again for the
        # real bounding box to place the divider and "WA" mark against.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bboxes = [t.get_window_extent(renderer=renderer) for t in lines]
        block_left_px = min(b.x0 for b in bboxes)
        block_top_px = max(b.y1 for b in bboxes)
        block_bottom_px = min(b.y0 for b in bboxes)
        center_px = (block_top_px + block_bottom_px) / 2
        half_h_px = max((block_top_px - block_bottom_px) / 2, 9) + 3

        divider_x_px = block_left_px - 10
        fig.add_artist(Line2D(
            [divider_x_px / fig.bbox.width] * 2,
            [(center_px - half_h_px) / fig.bbox.height, (center_px + half_h_px) / fig.bbox.height],
            transform=fig.transFigure, color=self.gridline, linewidth=1,
        ))
        mark = fig.text(
            (divider_x_px - 10) / fig.bbox.width, center_px / fig.bbox.height, "WA",
            transform=fig.transFigure, ha="right", va="center",
            color=self.accent, fontsize=21, fontweight="bold", family="serif",
        )

        # Third pass: the "WA" mark itself extends further left than the
        # divider by its own rendered width -- measure it to get the
        # lockup's *true* leftmost edge.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        mark_left_px = mark.get_window_extent(renderer=renderer).x0
        return mark_left_px / fig.bbox.width

    def draw_header(
        self, fig, eyebrow: str | None = None, title: str | None = None,
        subtitle: str | None = None, author: str | None = None,
        title_fontsize: float = 15, left_x_in: float = 0.28,
    ) -> None:
        """The full header band: eyebrow + serif title + subtitle at the
        top-left, the WA brand lockup at the top-right (see
        :meth:`draw_wa_lockup`) -- and reserves the figure's top margin via
        ``subplots_adjust`` so whatever axes are already in the figure
        (a single axes, a GridSpec, a polar plot) shrink to make room,
        without needing to know how they were created.

        Disables the figure's layout engine first (``set_layout_engine(None)``)
        -- :func:`mplsoccer.Pitch.draw` turns on a ``TightLayoutEngine`` by
        default, which silently re-runs on every subsequent draw/save and
        overrides ``subplots_adjust`` with its own recalculated margins,
        undoing the reserved header space the moment the figure is saved.
        Confirmed by rendering: without this, the title and the legend
        (top-left of the now "restored" full-size axes) draw on top of
        each other in the saved PNG despite ``subplots_adjust`` having
        already run.

        The lockup is drawn *first* and the title/subtitle truncated
        (measured, not guessed -- see :func:`_truncate_to_width`) to stop
        short of it, with an ellipsis -- confirmed by rendering a long
        title on a narrow (6in) figure: without this, the title ran
        straight through the lockup instead of stopping before it.
        """
        from matplotlib.font_manager import FontProperties

        fig.set_layout_engine(None)
        fig_w, fig_h = fig.get_size_inches()
        lockup_left = self.draw_wa_lockup(fig, author=author, x_in=left_x_in, y_in=0.24)

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        max_width_px = max((lockup_left - left_x_in / fig_w) * fig.bbox.width - 12, 20)

        y_in = 0.24
        if eyebrow:
            self.draw_eyebrow(fig, eyebrow, x_in=left_x_in, y_in=y_in)
            y_in += 0.30
        if title:
            title_prop = FontProperties(family="serif", weight="bold", size=title_fontsize)
            fitted = _truncate_to_width(fig, renderer, title, title_prop, max_width_px)
            fig.text(
                left_x_in / fig_w, 1 - y_in / fig_h, fitted, transform=fig.transFigure,
                ha="left", va="top", color=self.ink_primary, fontsize=title_fontsize,
                fontweight="bold", family="serif",
            )
            y_in += title_fontsize / 72 * 1.35
        if subtitle:
            subtitle_prop = FontProperties(size=10)
            fitted_subtitle = _truncate_to_width(fig, renderer, subtitle, subtitle_prop, max_width_px)
            fig.text(
                left_x_in / fig_w, 1 - y_in / fig_h, fitted_subtitle, transform=fig.transFigure,
                ha="left", va="top", color=self.ink_secondary, fontsize=10,
            )
            y_in += 0.26
        fig.subplots_adjust(top=max(0.5, 1 - (y_in + 0.15) / fig_h))

    def draw_footer(self, fig, source: str | None = None, author: str | None = None, fontsize: float = 8) -> None:
        """The footer band: ``source`` (e.g. a data-provider credit)
        bottom-left, and ``"{author} | Created on DD-MM-YYYY"`` bottom-right
        if ``author`` is given -- reserves the figure's bottom margin the
        same way :meth:`draw_header` reserves the top. A no-op if neither
        is given, same as the pre-existing :meth:`style_footer` behavior:
        a credit line is never defaulted. Also disables the figure's
        layout engine -- see :meth:`draw_header`'s docstring for why."""
        if not source and not author:
            return
        fig.set_layout_engine(None)
        fig_w, fig_h = fig.get_size_inches()
        # The footer text itself sits right at the bottom edge; the margin
        # reserved below the axes has to clear the axes' own tick labels
        # *and* the footer text, not just the footer text -- an axes'
        # x-tick labels render in the space subplots_adjust(bottom=...)
        # carves out, so too small a reserve here puts the footer text
        # directly on top of them.
        text_in = 0.16
        if source:
            fig.text(
                0.28 / fig_w, text_in / fig_h, source, transform=fig.transFigure,
                ha="left", va="bottom", color=self.ink_muted, fontsize=fontsize,
            )
        if author:
            stamp = f"{author} | Created on {date.today():%d-%m-%Y}"
            fig.text(
                1 - 0.28 / fig_w, text_in / fig_h, stamp, transform=fig.transFigure,
                ha="right", va="bottom", color=self.ink_muted, fontsize=fontsize,
            )
        fig.subplots_adjust(bottom=min(0.5, (text_in + 0.5) / fig_h))


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
    accent="#eda100",  # WA's light-mode brand amber, not dark mode's coral
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
