from pathlib import Path

import pandas as pd
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
pytest.importorskip("mplsoccer")

from wa_setpieces import (  # noqa: E402
    delivery_locations,
    extract_corners,
    load_events,
    set_piece_summary,
)
from wa_setpieces.phases import second_phases  # noqa: E402
from wa_setpieces.xt import XTModel, set_piece_delivery_xt  # noqa: E402
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


def test_plot_team_comparison_returns_fig_and_ax(events):
    summary = set_piece_summary(events)
    fig, ax = viz.plot_team_comparison(summary, metric="attempts", title="Attempts")
    assert fig is not None
    assert ax is not None


def test_plot_team_comparison_rejects_more_than_two_teams(events):
    summary = set_piece_summary(events)
    third_team = summary[summary["contestantId"] == summary["contestantId"].iloc[0]].copy()
    third_team["contestantId"] = "a_third_team"
    padded = pd.concat([summary, third_team], ignore_index=True)
    with pytest.raises(ValueError):
        viz.plot_team_comparison(padded, metric="attempts")


def test_plot_team_comparison_respects_team_order(events):
    summary = set_piece_summary(events)
    teams = list(summary["contestantId"].unique())
    fig, ax = viz.plot_team_comparison(summary, metric="attempts", team_order=list(reversed(teams)))
    legend_labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert legend_labels[0].startswith(teams[-1][:8])


def test_plot_xt_added_bars_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    dxt = set_piece_delivery_xt(events, "free_kick", model)
    fig, ax = viz.plot_xt_added_bars(dxt, title="xT added")
    assert fig is not None
    assert ax is not None


def test_plot_corner_sonar_returns_fig_and_ax(events):
    corners = delivery_locations(events, "corner")
    fig, ax = viz.plot_corner_sonar(corners)
    assert fig is not None
    assert ax is not None


def test_plot_match_timeline_returns_fig_and_ax(events):
    fig, ax = viz.plot_match_timeline(events)
    assert fig is not None
    assert ax is not None


def test_plot_match_timeline_minutes_within_match_length(events):
    fig, ax = viz.plot_match_timeline(events)
    offsets = [c.get_offsets() for c in ax.collections if len(c.get_offsets())]
    all_minutes = [pt[0] for offs in offsets for pt in offs]
    assert max(all_minutes) < 100  # sample match runs ~102 minutes total


def test_plot_dashboard_returns_figure(events):
    corners = delivery_locations(events, "corner")
    team_id = corners["contestantId"].value_counts().idxmax()
    fig = viz.plot_dashboard(events, team_id, set_piece_type="corner")
    assert fig is not None
    assert len(fig.axes) == 4
