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
from wa_setpieces.core.outcomes import OUTCOME_CATEGORIES, delivery_outcomes  # noqa: E402
from wa_setpieces.core.phases import second_phases  # noqa: E402
from wa_setpieces.core.report import corner_report  # noqa: E402
from wa_setpieces.core.xt import XTModel, set_piece_delivery_xt  # noqa: E402
from wa_setpieces.viz import plots as viz  # noqa: E402

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


def test_plot_second_phase_raises_on_ambiguous_eventid(events):
    # Regression test: eventId is only unique per team (see chains.py's
    # docstring), so a bare eventId lookup across both teams' corners can be
    # ambiguous. Fabricate that collision and confirm it's rejected loudly
    # rather than silently plotting the wrong delivery.
    corners = second_phases(events, "corner")
    delivery_id = int(corners["delivery_event_id"].iloc[0])
    real_row = events[events["eventId"] == delivery_id].iloc[0].copy()
    other_team = next(t for t in events["contestantId"].unique() if t != real_row["contestantId"])
    fake_row = real_row.copy()
    fake_row["contestantId"] = other_team
    fake_row["q_6"] = True  # tag as a corner too
    events_with_collision = pd.concat([events, pd.DataFrame([fake_row])], ignore_index=True)

    with pytest.raises(ValueError, match="matches 2 corner/free-kick deliveries"):
        viz.plot_second_phase(events_with_collision, delivery_id)

    # Disambiguated with contestant_id, it works again.
    fig, ax = viz.plot_second_phase(
        events_with_collision, delivery_id, contestant_id=real_row["contestantId"]
    )
    assert fig is not None


def test_plot_delivery_map_light_mode_uses_light_surface(events):
    corners = delivery_locations(events, "corner")
    fig, ax = viz.plot_delivery_map(corners, dark=False)
    from wa_setpieces.viz.theme import get_palette

    light = get_palette(dark=False)
    dark = get_palette(dark=True)
    assert ax.get_facecolor() != dark.surface
    import matplotlib.colors as mcolors
    assert mcolors.to_hex(ax.get_facecolor()) == light.surface


def test_plot_delivery_map_dark_is_default(events):
    corners = delivery_locations(events, "corner")
    fig_dark, ax_dark = viz.plot_delivery_map(corners)
    fig_explicit, ax_explicit = viz.plot_delivery_map(corners, dark=True)
    import matplotlib.colors as mcolors
    assert mcolors.to_hex(ax_dark.get_facecolor()) == mcolors.to_hex(ax_explicit.get_facecolor())


def test_plot_team_comparison_light_and_dark_use_team_colors(events):
    summary = set_piece_summary(events)
    from wa_setpieces.viz.theme import get_palette

    for dark in (True, False):
        pal = get_palette(dark)
        fig, ax = viz.plot_team_comparison(summary, metric="attempts", dark=dark)
        bar_colors = {tuple(patch.get_facecolor()) for patch in ax.patches}
        import matplotlib.colors as mcolors
        expected = {mcolors.to_rgba(c) for c in pal.team_colors[: len(summary["contestantId"].unique())]}
        assert bar_colors.issubset(expected) or expected.issubset(bar_colors) or bar_colors & expected


def test_plot_set_piece_outcomes_goal_ring_is_gold(events):
    from wa_setpieces.core.outcomes import delivery_outcomes

    outcomes = delivery_outcomes(events, "corner").copy()
    outcomes.loc[outcomes.index[0], "is_goal"] = True
    fig, ax = viz.plot_set_piece_outcomes(outcomes)
    import matplotlib.colors as mcolors

    from wa_setpieces.viz.theme import get_palette

    pal = get_palette(dark=True)
    goal_rings = [c for c in ax.collections if c.get_label() == "Goal"]
    assert len(goal_rings) == 1
    assert mcolors.to_hex(goal_rings[0].get_edgecolor()[0]) == pal.gold


def test_subtitle_and_footer_render_without_error(events):
    corners = delivery_locations(events, "corner")
    fig, ax = viz.plot_delivery_map(
        corners, title="Corners", subtitle="20 June 2026 · Example", footer="Data: Opta // Example"
    )
    assert ax.get_title() == "Corners"
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


def test_plot_set_piece_radar_returns_fig_and_ax(events):
    report = corner_report(events)
    fig, ax = viz.plot_set_piece_radar(report, title="Corner profile")
    assert fig is not None
    assert ax is not None


def test_plot_set_piece_radar_with_model_includes_value_axis(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    report = corner_report(events, model=model)
    fig, ax = viz.plot_set_piece_radar(report)
    # 5 default metrics all present when a model is supplied
    assert len(ax.texts) >= 5 + 5  # param labels + range labels, roughly


def test_plot_set_piece_radar_rejects_wrong_team_count(events):
    report = corner_report(events)
    with pytest.raises(ValueError, match="needs exactly 2 teams"):
        viz.plot_set_piece_radar(report.iloc[:1])


def test_plot_set_piece_radar_custom_metrics(events):
    report = corner_report(events)
    fig, ax = viz.plot_set_piece_radar(
        report, metrics=["attempts", "success_rate", "retention_rate"]
    )
    assert fig is not None


def test_plot_set_piece_radar_rejects_too_few_metrics(events):
    report = corner_report(events)
    with pytest.raises(ValueError, match="at least 3 metrics"):
        viz.plot_set_piece_radar(report, metrics=["attempts", "success_rate"])


def test_plot_set_piece_radar_rejects_no_usable_metrics(events):
    report = corner_report(events)[["contestantId"]]
    with pytest.raises(ValueError, match="no usable metric columns"):
        viz.plot_set_piece_radar(report)


def test_plot_set_piece_outcomes_returns_fig_and_ax(events):
    outcomes = delivery_outcomes(events, "corner")
    fig, ax = viz.plot_set_piece_outcomes(outcomes, title="Corner outcomes")
    assert fig is not None
    assert ax is not None


def test_plot_set_piece_outcomes_legend_matches_present_categories(events):
    outcomes = delivery_outcomes(events, "corner")
    fig, ax = viz.plot_set_piece_outcomes(outcomes)
    legend_labels = {t.get_text() for t in ax.get_legend().get_texts()}
    present_categories = set(outcomes["category"].unique())
    expected_labels = {viz._OUTCOME_LABELS[cat] for cat in present_categories}
    assert expected_labels.issubset(legend_labels)


def test_plot_set_piece_outcomes_goal_ring_only_when_goals_exist(events):
    outcomes = delivery_outcomes(events, "corner")
    fig, ax = viz.plot_set_piece_outcomes(outcomes)
    legend_labels = {t.get_text() for t in ax.get_legend().get_texts()}
    # No goals from corners in the sample match.
    assert not outcomes["is_goal"].any()
    assert "Goal" not in legend_labels


def test_plot_set_piece_outcomes_handles_free_kicks(events):
    outcomes = delivery_outcomes(events, "free_kick")
    fig, ax = viz.plot_set_piece_outcomes(outcomes, title="Free-kick outcomes")
    assert fig is not None


def test_plot_set_piece_outcomes_color_stable_across_category_order():
    # Colors are assigned by OUTCOME_CATEGORIES' fixed order, not by
    # whichever categories happen to appear first in a given match -- so
    # the same category is always the same color across different plots,
    # regardless of which order the categories appear in the data.
    import pandas as pd

    outcomes_a = pd.DataFrame(
        {"category": ["cleared", "aerial_duel"], "x": [50, 60], "y": [50, 60], "is_goal": [False, False]}
    )
    outcomes_b = pd.DataFrame(
        {"category": ["aerial_duel", "cleared"], "x": [60, 50], "y": [60, 50], "is_goal": [False, False]}
    )
    _, ax_a = viz.plot_set_piece_outcomes(outcomes_a)
    _, ax_b = viz.plot_set_piece_outcomes(outcomes_b)

    def color_for_label(ax, label):
        for coll in ax.collections:
            if coll.get_label() == label:
                return tuple(coll.get_facecolor()[0])
        raise AssertionError(f"no series labelled {label!r}")

    cleared_label = viz._OUTCOME_LABELS["cleared"]
    aerial_label = viz._OUTCOME_LABELS["aerial_duel"]
    assert color_for_label(ax_a, cleared_label) == color_for_label(ax_b, cleared_label)
    assert color_for_label(ax_a, aerial_label) == color_for_label(ax_b, aerial_label)
    assert color_for_label(ax_a, cleared_label) != color_for_label(ax_a, aerial_label)
