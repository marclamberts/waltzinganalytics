from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import XTModel, load_events, render_html_report, save_table, save_tables
from wa_setpieces.cli import main
from wa_setpieces.reporting import corner_report_html, opponent_scouting_report_html

DATA = Path(__file__).parent / "data" / "sample_match.json"


def test_full_xt_persistence_and_evaluation(tmp_path):
    events = load_events(DATA).events
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    path = tmp_path / "model.npz"
    model.save(path)
    loaded = XTModel.load(path)
    assert loaded.metadata["event_count"] == len(events)
    assert loaded.evaluate(events)["shots"] > 0


def test_html_report_escapes_title():
    html = render_html_report("A < B", {"Summary": pd.DataFrame({"value": [1]})})
    assert "A &lt; B" in html and "<table" in html


def test_cli_summary_json(tmp_path):
    output = tmp_path / "summary.json"
    assert main(["summary", str(DATA), "--output", str(output), "--format", "json"]) == 0
    assert output.exists() and "contestantId" in output.read_text()


def test_cli_workflow_xlsx_writes_one_file_per_table(tmp_path):
    pytest.importorskip("openpyxl")
    output = tmp_path / "workflow"
    assert main(["workflow", str(DATA), "--type", "corner", "--format", "xlsx", "--output", str(output)]) == 0
    assert (output / "summary.xlsx").exists()
    assert not (output / "summary.csv").exists()


def test_cli_report_corner_uses_curated_html(tmp_path):
    output = tmp_path / "report.html"
    assert main(["report", str(DATA), "--type", "corner", "--output", str(output)]) == 0
    html = output.read_text()
    assert "Team report" in html and "Outcome breakdown" in html and "Routine usage" in html


def test_cli_report_non_corner_falls_back_to_generic_dump(tmp_path):
    output = tmp_path / "report.html"
    assert main(["report", str(DATA), "--type", "throw_in", "--output", str(output)]) == 0
    assert "Throw In report" in output.read_text()


def test_cli_scout_writes_opponent_report(tmp_path):
    events = load_events(DATA).events
    opponent = events["contestantId"].dropna().unique()[0]
    output = tmp_path / "scout.html"
    assert main(["scout", str(DATA), "--opponent", opponent, "--output", str(output)]) == 0
    html = output.read_text()
    assert "Conceded by routine type" in html


def test_cli_season_summary(tmp_path):
    match_a = tmp_path / "match_a.json"
    match_b = tmp_path / "match_b.json"
    match_a.write_text(DATA.read_text())
    match_b.write_text(DATA.read_text())
    output = tmp_path / "season_summary.csv"
    assert main(["season", str(match_a), str(match_b), "--action", "summary", "--output", str(output)]) == 0
    result = pd.read_csv(output)
    assert (result["matches"] == 2).all()


def test_cli_season_season_report(tmp_path):
    match_a = tmp_path / "match_a.json"
    match_b = tmp_path / "match_b.json"
    match_a.write_text(DATA.read_text())
    match_b.write_text(DATA.read_text())
    output = tmp_path / "season_report.csv"
    assert main([
        "season", str(match_a), str(match_b), "--action", "season-report",
        "--type", "corner", "--output", str(output),
    ]) == 0
    result = pd.read_csv(output)
    assert "matchId" not in result.columns
    single = load_events(DATA).events
    from wa_setpieces import corner_report
    assert result["attempts"].sum() == 2 * single.pipe(corner_report)["attempts"].sum()


def test_cli_season_rejects_duplicate_filenames(tmp_path):
    output = tmp_path / "out.csv"
    with pytest.raises(ValueError, match="duplicate matchId"):
        main(["season", str(DATA), str(DATA), "--action", "summary", "--output", str(output)])


def test_save_table_csv_round_trips(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    path = save_table(df, tmp_path / "out.csv")
    assert path == tmp_path / "out.csv"
    assert pd.read_csv(path).equals(df)


def test_save_table_xlsx_round_trips(tmp_path):
    pytest.importorskip("openpyxl")
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    path = save_table(df, tmp_path / "out.xlsx")
    assert pd.read_excel(path).equals(df)


def test_save_table_creates_parent_directories(tmp_path):
    df = pd.DataFrame({"a": [1]})
    path = save_table(df, tmp_path / "nested" / "dir" / "out.csv")
    assert path.exists()


def test_save_table_rejects_unsupported_extension(tmp_path):
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="unsupported file extension"):
        save_table(df, tmp_path / "out.txt")


def test_save_table_xlsx_without_engine_raises_clear_error(tmp_path, monkeypatch):
    df = pd.DataFrame({"a": [1]})

    def fake_to_excel(self, *args, **kwargs):
        raise ImportError("no engine")

    monkeypatch.setattr(pd.DataFrame, "to_excel", fake_to_excel)
    with pytest.raises(ImportError, match="xlsx"):
        save_table(df, tmp_path / "out.xlsx")


def test_save_tables_writes_one_file_per_table(tmp_path):
    tables = {"team_report": pd.DataFrame({"a": [1]}), "player_report": pd.DataFrame({"b": [2]})}
    paths = save_tables(tables, tmp_path / "out", fmt="csv")
    assert set(paths) == {"team_report", "player_report"}
    for name, path in paths.items():
        assert path == tmp_path / "out" / f"{name}.csv"
        assert path.exists()


def test_corner_report_html_without_model_has_core_tables():
    events = load_events(DATA).events
    html = corner_report_html(events, include_figures=False)
    assert "Team report" in html
    assert "Outcome breakdown" in html
    assert "Routine usage" in html
    # team_rating still runs on success_rate/retention_rate alone, but the
    # report table itself must not carry an added-value column without a model.
    assert "avg_added_value" not in html


def test_corner_report_html_with_model_includes_added_value():
    events = load_events(DATA).events
    model = XTModel.fit(events, x_bins=8, y_bins=6)
    html = corner_report_html(events, model=model, include_figures=False)
    assert "Team rating" in html
    assert "avg_added_value" in html


def test_corner_report_html_include_figures_requires_viz_extra():
    pytest.importorskip("matplotlib")
    pytest.importorskip("mplsoccer")
    import matplotlib
    matplotlib.use("Agg")
    events = load_events(DATA).events
    html = corner_report_html(events, include_figures=True)
    assert "Delivery map" in html
    assert "Outcome shot map" in html


def test_opponent_scouting_report_html_has_conceding_tables():
    events = load_events(DATA).events
    opponent_id = events["contestantId"].dropna().unique()[0]
    html = opponent_scouting_report_html(events, opponent_id, "corner", include_figures=False)
    assert "Conceded by routine type" in html
    assert "Conceded by destination zone" in html
    assert "Aerial duel record" in html


def test_opponent_scouting_report_html_omits_aerial_duel_for_non_phase_types():
    events = load_events(DATA).events
    opponent_id = events["contestantId"].dropna().unique()[0]
    html = opponent_scouting_report_html(events, opponent_id, "throw_in", include_figures=False)
    assert "Conceded by routine type" in html
    assert "Aerial duel record" not in html


def test_opponent_scouting_report_html_uses_team_name_in_title():
    events = load_events(DATA).events
    opponent_id = events["contestantId"].dropna().unique()[0]
    html = opponent_scouting_report_html(events, opponent_id, "corner", team_name="Rivals FC", include_figures=False)
    assert "Rivals FC" in html


def test_opponent_scouting_report_html_include_figures_requires_viz_extra():
    pytest.importorskip("matplotlib")
    pytest.importorskip("mplsoccer")
    import matplotlib
    matplotlib.use("Agg")
    events = load_events(DATA).events
    opponent_id = events["contestantId"].dropna().unique()[0]
    html = opponent_scouting_report_html(events, opponent_id, "corner", include_figures=True)
    assert "Conceded by routine" in html
    assert "Shots conceded by zone" in html
