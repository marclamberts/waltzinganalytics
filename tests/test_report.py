from pathlib import Path

import pytest

from wa_setpieces import load_events
from wa_setpieces.core.report import corner_report, free_kick_report, set_piece_report
from wa_setpieces.core.xt import XTModel

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_corner_report_has_phase_and_retention_columns(events):
    report = corner_report(events)
    assert len(report) == 2
    assert {
        "contestantId", "attempts", "successful", "success_rate",
        "second_phases", "second_phase_goals", "second_phase_rate", "retention_rate",
    }.issubset(report.columns)


def test_free_kick_report_matches_corner_report_shape(events):
    report = free_kick_report(events)
    assert len(report) == 2
    assert "second_phase_rate" in report.columns


def test_report_with_model_adds_value_columns(events, model):
    report = corner_report(events, model=model)
    assert {"total_added_value", "avg_added_value", "goals"}.issubset(report.columns)


def test_report_without_model_has_no_value_columns(events):
    report = corner_report(events)
    assert "total_added_value" not in report.columns


def test_throw_in_report_has_no_phase_columns(events):
    # throw-ins aren't a phase type (phases.py only covers corner/free_kick)
    report = set_piece_report(events, "throw_in")
    assert "second_phase_rate" not in report.columns
    assert "retention_rate" in report.columns


def test_report_rejects_value_for_non_phase_type(events, model):
    with pytest.raises(ValueError):
        set_piece_report(events, "throw_in", model=model)


def test_report_attempts_match_known_totals(events):
    report = corner_report(events)
    assert report["attempts"].sum() == 9  # known corner count in the sample match
