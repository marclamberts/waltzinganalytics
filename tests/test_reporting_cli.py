from pathlib import Path

import pandas as pd

from wa_setpieces import XTModel, load_events, render_html_report
from wa_setpieces.cli import main

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
