from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import XTModel, load_events, render_html_report
from wa_setpieces.cli import main
from wa_setpieces.reporting import corner_report_html

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
