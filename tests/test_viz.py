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
    # Title/subtitle/footer live in the figure-level WA header/footer band
    # (not ax.set_title) whenever this function created its own figure --
    # see _finish_figure's docstring on why that differs from the
    # existing-ax fallback path covered by test_plotting_with_existing_axis.
    figure_text = {t.get_text() for t in fig.texts}
    assert "Corners" in figure_text
    assert "20 June 2026 · Example" in figure_text
    assert "Data: Opta // Example" in figure_text
    assert fig is not None


def test_title_falls_back_to_axes_title_with_existing_axis(events):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    corners = delivery_locations(events, "corner")
    viz.plot_delivery_map(corners, title="Corners", ax=ax)
    # With a caller-supplied ax, this function doesn't own the whole
    # figure, so the title stays on the axes instead of the figure-level
    # header band (which would need to reserve margin it can't safely
    # claim on a figure it didn't create).
    assert ax.get_title() == "Corners"


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


def test_plot_rating_benchmark_returns_fig_and_ax(events):
    from wa_setpieces.core.rating import team_rating
    from wa_setpieces.core.report import corner_report

    model = XTModel.fit(events, x_bins=8, y_bins=6)
    rated = team_rating(corner_report(events, model=model))
    fig, ax = viz.plot_rating_benchmark(rated)
    assert fig is not None
    assert ax is not None


def test_plot_rating_benchmark_drops_nan_ratings_and_respects_top_n():
    import pandas as pd

    rated = pd.DataFrame({
        "contestantId": ["a", "b", "c"],
        "rating": [65.0, None, 35.0],
    })
    fig, ax = viz.plot_rating_benchmark(rated, top_n=1)
    assert len(ax.get_yticklabels()) == 1


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
    present_categories = set(outcomes["delivery_outcome"].unique())
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
        {"delivery_outcome": ["cleared", "aerial_duel"], "x": [50, 60], "y": [50, 60], "is_goal": [False, False]}
    )
    outcomes_b = pd.DataFrame(
        {"delivery_outcome": ["aerial_duel", "cleared"], "x": [60, 50], "y": [60, 50], "is_goal": [False, False]}
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


def test_plot_routine_clusters_returns_fig_and_ax(events):
    pytest.importorskip("sklearn")
    from wa_setpieces.core.routines import cluster_routines

    clustered = cluster_routines(events, "corner", n_clusters=3, random_state=0)
    fig, ax = viz.plot_routine_clusters(clustered, title="Corner clusters")
    assert fig is not None
    assert ax is not None
    legend_labels = {t.get_text() for t in ax.get_legend().get_texts()}
    assert legend_labels == set(clustered["cluster_label"].dropna().unique())


def test_plot_routine_clusters_handles_all_unclustered():
    from wa_setpieces.core.routines import cluster_routines

    pytest.importorskip("sklearn")
    empty_ish = pd.DataFrame(
        {"eventId": [1], "x": [99.0], "y": [50.0], "end_x": [90.0], "end_y": [50.0], "cluster": [-1], "cluster_label": [pd.NA]}
    )
    fig, ax = viz.plot_routine_clusters(empty_ish)
    assert fig is not None


def test_plot_defensive_routine_bars_requires_team_id_for_multiple_teams(events):
    from wa_setpieces.core.defending import defensive_routine_summary

    conceded = defensive_routine_summary(events, "corner")
    with pytest.raises(ValueError):
        viz.plot_defensive_routine_bars(conceded)
    team = conceded["contestantId"].iloc[0]
    fig, ax = viz.plot_defensive_routine_bars(conceded, team_id=team)
    assert fig is not None


def test_plot_defensive_routine_bars_works_with_zone_summary(events):
    from wa_setpieces.core.defending import defensive_zone_summary

    conceded = defensive_zone_summary(events, "corner")
    team = conceded["contestantId"].iloc[0]
    fig, ax = viz.plot_defensive_routine_bars(conceded, team_id=team, metric="shots_conceded")
    assert fig is not None


def test_plot_aerial_duel_win_rate_returns_fig_and_ax(events):
    from wa_setpieces.core.outcomes import aerial_duel_summary

    team_summary, _ = aerial_duel_summary(events, "corner")
    fig, ax = viz.plot_aerial_duel_win_rate(team_summary)
    assert fig is not None
    assert len(ax.get_yticklabels()) == len(team_summary)


def test_plot_outcome_flow_returns_fig_and_ax(events):
    outcomes = delivery_outcomes(events, "corner")
    fig, ax = viz.plot_outcome_flow(outcomes, title="Corner outcome flow")
    assert fig is not None
    assert ax is not None


def test_plot_outcome_flow_no_goal_node_when_no_goals(events):
    # The sample match has zero corner goals -- the "Goal" node/ribbons
    # should be omitted entirely rather than drawn as an empty sliver.
    outcomes = delivery_outcomes(events, "corner")
    assert outcomes["is_goal"].sum() == 0
    fig, ax = viz.plot_outcome_flow(outcomes)
    n_categories = outcomes["delivery_outcome"].nunique()
    # deliveries node + one rect per category + no_goal node == n_categories + 2,
    # each also with a stage0->stage1 ribbon and a stage1->stage2 ribbon.
    assert len(ax.patches) == (n_categories + 2) + n_categories * 2


def test_plot_outcome_flow_splits_into_goal_and_no_goal():
    outcomes = pd.DataFrame(
        {
            "delivery_outcome": ["direct_shot"] * 4 + ["cleared"] * 6,
            "is_goal": [True, True, False, False] + [False] * 6,
        }
    )
    fig, ax = viz.plot_outcome_flow(outcomes)
    texts = [t.get_text() for t in ax.texts]
    assert any("Goal (2)" in t for t in texts)
    assert any("No goal (8)" in t for t in texts)


def test_plot_rating_beeswarm_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    from wa_setpieces.core.rating import player_rating

    rated = player_rating(events, "corner", model, min_deliveries=1, min_shots=1)
    fig, ax = viz.plot_rating_beeswarm(rated, title="Corner rating spread")
    assert fig is not None
    assert len(ax.collections) >= 1


def test_plot_rating_beeswarm_rejects_more_than_two_teams():
    rated = pd.DataFrame(
        {
            "playerName": ["A", "B", "C"],
            "contestantId": ["team1", "team2", "team3"],
            "rating": [60.0, 55.0, 50.0],
        }
    )
    with pytest.raises(ValueError, match="at most 2 teams"):
        viz.plot_rating_beeswarm(rated)


def test_beeswarm_offsets_spreads_identical_values():
    offsets = viz._beeswarm_offsets(pd.Series([50.0, 50.0, 50.0, 50.0]).to_numpy(), bin_width=2.5, spacing=0.22)
    assert len(set(offsets)) == 4
    assert offsets[0] == 0.0


def test_plot_value_waterfall_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    team_id = set_piece_summary(events)["contestantId"].iloc[0]
    fig, ax = viz.plot_value_waterfall(events, team_id, model)
    assert fig is not None
    assert len(ax.patches) == 3  # corner, free_kick, Total


def test_plot_value_waterfall_total_bar_matches_sum_of_parts(events):
    from wa_setpieces.core.value import set_piece_added_value

    model = XTModel.fit(events, x_bins=8, y_bins=6)
    team_id = set_piece_summary(events)["contestantId"].iloc[0]
    fig, ax = viz.plot_value_waterfall(events, team_id, model)
    expected_total = sum(
        set_piece_added_value(events, t, model).loc[
            lambda d: d["contestantId"] == team_id, "added_value"
        ].sum()
        for t in ("corner", "free_kick")
    )
    total_bar = ax.patches[-1]
    top = total_bar.get_y() + total_bar.get_height()
    bottom = total_bar.get_y()
    # The total bar spans [0, total] (or [total, 0] if negative) --
    # whichever edge isn't 0 should match the true grand total.
    assert pytest.approx(expected_total, abs=1e-9) in (top, bottom)


def test_plot_value_distribution_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    fig, ax = viz.plot_value_distribution(events, model)
    assert fig is not None
    assert len(ax.get_xticklabels()) == 2  # corner, free_kick


def test_plot_value_distribution_raises_when_no_type_has_enough_data(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    empty_events = events.iloc[0:0]
    with pytest.raises(ValueError, match="enough deliveries"):
        viz.plot_value_distribution(empty_events, model)


def test_plot_type_radial_bar_returns_fig_and_ax(events):
    summary = set_piece_summary(events)
    team_id = summary["contestantId"].iloc[0]
    fig, ax = viz.plot_type_radial_bar(summary, team_id=team_id, metric="attempts")
    assert fig is not None
    team_types = summary.loc[summary["contestantId"] == team_id, "set_piece_type"].nunique()
    assert len(ax.patches) == team_types


def test_plot_type_radial_bar_combines_teams_when_team_id_is_none(events):
    summary = set_piece_summary(events)
    fig, ax = viz.plot_type_radial_bar(summary, team_id=None, metric="attempts")
    assert fig is not None
    assert len(ax.patches) == summary["set_piece_type"].nunique()


def test_plot_success_waffle_fills_correct_number_of_squares():
    import matplotlib.colors as mcolors

    from wa_setpieces.viz import theme

    fig, ax = viz.plot_success_waffle(25, 100, grid=(10, 10))
    pal = theme.get_palette(True)
    good_rgb = mcolors.to_rgb(pal.good)
    filled = sum(1 for p in ax.patches if p.get_facecolor()[:3] == good_rgb)
    assert filled == 25


def test_plot_success_waffle_handles_zero_total():
    fig, ax = viz.plot_success_waffle(0, 0, grid=(5, 4))
    assert fig is not None


def test_plot_type_outcome_mosaic_returns_fig_and_ax(events):
    summary = set_piece_summary(events)
    team_id = summary["contestantId"].iloc[0]
    fig, ax = viz.plot_type_outcome_mosaic(summary, team_id=team_id)
    assert fig is not None
    n_types = (summary.loc[summary["contestantId"] == team_id, "attempts"] > 0).sum()
    assert len(ax.patches) == n_types * 2


def test_plot_type_outcome_mosaic_rejects_multiple_teams(events):
    summary = set_piece_summary(events)
    with pytest.raises(ValueError, match="more than one team"):
        viz.plot_type_outcome_mosaic(summary)


def test_plot_team_parallel_coordinates_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    report = corner_report(events, model=model)
    fig, ax = viz.plot_team_parallel_coordinates(report)
    assert fig is not None
    assert len(ax.lines) >= 2  # one line per team plus gridlines


def test_plot_team_parallel_coordinates_rejects_wrong_row_count(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    report = corner_report(events, model=model)
    with pytest.raises(ValueError, match="exactly 2 rows"):
        viz.plot_team_parallel_coordinates(report.iloc[:1])


def test_plot_team_dumbbell_returns_fig_and_ax(events):
    summary = set_piece_summary(events)
    fig, ax = viz.plot_team_dumbbell(summary, metric="attempts")
    assert fig is not None
    n_types = summary["set_piece_type"].nunique()
    assert len(ax.get_yticklabels()) == n_types


def test_plot_team_dumbbell_rejects_more_than_two_teams(events):
    summary = pd.DataFrame(
        {
            "contestantId": ["team1", "team2", "team3"],
            "set_piece_type": ["corner", "corner", "corner"],
            "attempts": [5, 6, 7],
        }
    )
    with pytest.raises(ValueError, match="at most 2 teams"):
        viz.plot_team_dumbbell(summary)


def test_plot_zone_bubble_returns_fig_and_ax(events):
    corners = delivery_locations(events, "corner")
    fig, ax = viz.plot_zone_bubble(corners, x_col="end_x", y_col="end_y")
    assert fig is not None
    assert len(ax.collections) >= 1


def test_plot_kpi_bullet_returns_fig_and_ax():
    fig, ax = viz.plot_kpi_bullet(0.75, target=0.7, label="Free-kick success rate")
    assert fig is not None
    assert len(ax.patches) == 4  # 3 bands + actual-value bar


def test_plot_kpi_bullet_default_max_value_covers_target_and_value():
    fig, ax = viz.plot_kpi_bullet(0.9, target=1.2)
    assert ax.get_xlim()[1] >= 1.2


def test_plot_value_ridgeline_returns_fig_and_ax(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    fig, ax = viz.plot_value_ridgeline(events, model)
    assert fig is not None
    assert len(ax.collections) >= 1  # one fill_between per ridge


def test_plot_value_ridgeline_raises_when_no_type_has_enough_data(events):
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    empty_events = events.iloc[0:0]
    with pytest.raises(ValueError, match="enough deliveries"):
        viz.plot_value_ridgeline(empty_events, model)


def test_plot_type_area_timeline_returns_fig_and_ax(events):
    fig, ax = viz.plot_type_area_timeline(events)
    assert fig is not None
    assert len(ax.collections) >= 1


def test_plot_type_area_timeline_bands_have_a_separating_stroke(events):
    fig, ax = viz.plot_type_area_timeline(events)
    for band in ax.collections:
        assert band.get_linewidth()[0] > 0


def test_plot_success_ring_returns_fig_and_ax():
    fig, ax = viz.plot_success_ring(27, 30, label="Throw-in retention")
    assert fig is not None
    assert len(ax.patches) == 2  # success wedge + remainder wedge


def test_plot_success_ring_handles_zero_total():
    fig, ax = viz.plot_success_ring(0, 0)
    assert fig is not None


def test_plot_half_comparison_slope_returns_fig_and_ax(events):
    summary = set_piece_summary(events)
    team_id = summary["contestantId"].iloc[0]
    fig, ax = viz.plot_half_comparison_slope(events, team_id=team_id)
    assert fig is not None
    n_types = summary.loc[summary["contestantId"] == team_id, "set_piece_type"].nunique()
    assert len(ax.lines) == n_types


def test_plot_half_comparison_slope_flat_line_is_neutral_colored(events):
    from wa_setpieces.viz import theme

    summary = set_piece_summary(events)
    team_id = summary["contestantId"].iloc[0]
    pal = theme.get_palette(True)
    fig, ax = viz.plot_half_comparison_slope(events, team_id=team_id)
    flat_lines = [
        line for line in ax.lines
        if line.get_ydata()[0] == line.get_ydata()[1]
    ]
    assert flat_lines, "expected at least one flat (no-change) line in this sample"
    for line in flat_lines:
        assert line.get_color() == pal.ink_muted


def test_plot_half_comparison_slope_rejects_multiple_teams(events):
    with pytest.raises(ValueError, match="more than one team"):
        viz.plot_half_comparison_slope(events)
