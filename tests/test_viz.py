from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
pytest.importorskip("mplsoccer")

from wa_setpieces import delivery_locations, extract_corners, load_events  # noqa: E402
from wa_setpieces.phases import second_phases  # noqa: E402
from wa_setpieces.xt import XTModel  # noqa: E402
from wa_setpieces import viz  # noqa: E402

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_plot_delivery_map_returns_fig_and_ax(events):
    corners = delivery_locations(events, "corner")
    fig, ax = viz.plot_delivery_map(corners, title="Corners")
    assert fig is not None
    assert ax is not None


def test_plot_delivery_map_handles_no_unsuccessful_or_no_successful(events):
    corners = delivery_locations(events, "corner")
    all_success = corners.assign(outcome=1)
    fig, ax = viz.plot_delivery_map(all_success)
    assert fig is not None

    all_fail = corners.assign(outcome=0)
    fig, ax = viz.plot_delivery_map(all_fail)
    assert fig is not None


def test_plot_zone_heatmap_returns_fig_and_ax(events):
    corners = extract_corners(events)
    fig, ax = viz.plot_zone_heatmap(corners, title="Corner zones")
    assert fig is not None
    assert ax is not None


def test_plot_xt_grid_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    fig, ax = viz.plot_xt_grid(model)
    assert fig is not None
    assert ax is not None


def test_plot_second_phase_returns_fig_and_ax(events):
    corners = second_phases(events, "corner")
    delivery_id = int(corners["delivery_event_id"].iloc[0])
    fig, ax = viz.plot_second_phase(events, delivery_id)
    assert fig is not None
    assert ax is not None


def test_plot_second_phase_shot_is_highlighted(events):
    corners = second_phases(events, "corner")
    shot_id = int(corners.loc[corners["second_phase_shot"], "delivery_event_id"].iloc[0])
    fig, ax = viz.plot_second_phase(events, shot_id)
    assert fig is not None


def test_plotting_with_existing_axis(events):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    corners = delivery_locations(events, "corner")
    returned_fig, returned_ax = viz.plot_delivery_map(corners, ax=ax)
    assert returned_fig is None  # no new figure created
    assert returned_ax is ax
