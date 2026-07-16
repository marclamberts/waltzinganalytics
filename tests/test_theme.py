import re

import pytest

matplotlib = pytest.importorskip("matplotlib")

from wa_setpieces import theme  # noqa: E402

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
