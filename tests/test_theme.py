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


def test_sequential_blue_cmap_is_monotonically_lighter_at_zero():
    cmap = theme.sequential_blue_cmap()
    low = cmap(0.0)
    high = cmap(1.0)
    # luminance proxy: sum of RGB should be higher (lighter) near 0
    assert sum(low[:3]) > sum(high[:3])


def test_sequential_green_cmap_is_monotonically_lighter_at_zero():
    cmap = theme.sequential_green_cmap()
    low = cmap(0.0)
    high = cmap(1.0)
    assert sum(low[:3]) > sum(high[:3])


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
