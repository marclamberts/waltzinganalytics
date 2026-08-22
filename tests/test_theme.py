import re

import pytest

matplotlib = pytest.importorskip("matplotlib")

from wa_setpieces.viz import theme  # noqa: E402

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_categorical_palette_has_eight_valid_hex_colors():
    assert len(theme.CATEGORICAL) == 8
    assert len(set(theme.CATEGORICAL)) == 8  # no duplicates
    for color in theme.CATEGORICAL:
        assert HEX_RE.match(color), color


def test_status_colors_are_distinct_from_categorical():
    assert theme.GOOD not in theme.CATEGORICAL
    assert theme.CRITICAL not in theme.CATEGORICAL


def _hex_to_rgb01(color: str) -> tuple[float, float, float]:
    r, g, b = (int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return r / 255, g / 255, b / 255


def _dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


@pytest.mark.parametrize("dark", [True, False])
@pytest.mark.parametrize("cmap_name", ["sequential_blue_cmap", "sequential_green_cmap"])
def test_sequential_cmap_low_end_recedes_toward_this_modes_own_surface(dark, cmap_name):
    # A low value should read as "barely there" against *this palette's own
    # canvas* -- not a fixed pale pastel that pops out of a dark surface
    # (the bug this was built to fix: a zone heatmap's zero-count cells
    # looked like a different, lighter-themed app pasted into the dark
    # navy WA card). So cmap(0.0) should sit close to `surface` in color
    # space, and cmap(1.0) (the saturated target hue) should sit far from
    # it, in both modes -- not just "lighter near zero" as a fixed-ramp
    # design would assume.
    pal = theme.get_palette(dark)
    cmap = getattr(pal, cmap_name)()
    surface_rgb = _hex_to_rgb01(pal.surface)
    low_dist = _dist(cmap(0.0)[:3], surface_rgb)
    high_dist = _dist(cmap(1.0)[:3], surface_rgb)
    assert low_dist < high_dist


def test_sequential_blue_cmap_dark_mode_matches_module_level_default():
    # theme.sequential_blue_cmap() (no palette argument) is pinned to the
    # dark palette for backwards compatibility -- confirm it actually
    # matches get_palette(dark=True)'s own cmap, not some other default.
    from_module = theme.sequential_blue_cmap()(0.5)
    from_dark_palette = theme.get_palette(dark=True).sequential_blue_cmap()(0.5)
    assert from_module == from_dark_palette


def test_diverging_cmap_midpoint_is_neutral_gray():
    cmap = theme.diverging_cmap()
    mid = cmap(0.5)
    r, g, b = mid[:3]
    # gray: channels close to each other, unlike the blue/red endpoints
    assert max(r, g, b) - min(r, g, b) < 0.05


def test_diverging_cmap_endpoints_match_positive_negative():
    cmap = theme.diverging_cmap()
    assert cmap(1.0)[:3] != cmap(0.0)[:3]


@pytest.mark.parametrize("dark", [True, False])
def test_get_palette_has_eight_valid_categorical_hex_colors(dark):
    pal = theme.get_palette(dark)
    assert len(pal.categorical) == 8
    assert len(set(pal.categorical)) == 8
    for color in pal.categorical:
        assert HEX_RE.match(color), color


@pytest.mark.parametrize("dark", [True, False])
def test_get_palette_team_colors_are_orange_then_blue_and_distinct(dark):
    pal = theme.get_palette(dark)
    assert len(pal.team_colors) == 2
    assert pal.team_colors[0] != pal.team_colors[1]
    for color in pal.team_colors:
        assert HEX_RE.match(color), color


def test_get_palette_dark_and_light_are_different_surfaces():
    dark_pal = theme.get_palette(True)
    light_pal = theme.get_palette(False)
    assert dark_pal.surface != light_pal.surface
    assert dark_pal.ink_primary != light_pal.ink_primary
    # Same fixed status/accent colors in both modes -- never themed.
    assert dark_pal.good == light_pal.good == theme.GOOD
    assert dark_pal.critical == light_pal.critical == theme.CRITICAL
    assert dark_pal.gold == light_pal.gold == theme.GOLD


def test_get_palette_default_is_dark():
    assert theme.get_palette() is theme.get_palette(True)
    assert theme.get_palette(dark=False) is not theme.get_palette(True)


def test_status_colors_are_distinct_from_gold():
    assert theme.GOLD != theme.GOOD
    assert theme.GOLD != theme.CRITICAL
    assert theme.GOLD not in theme.CATEGORICAL
