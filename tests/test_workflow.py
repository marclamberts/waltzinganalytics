from pathlib import Path

import pytest

from wa_setpieces import load_events
from wa_setpieces.core.workflow import SetPieceWorkflow, run_workflow
from wa_setpieces.core.xt import XTModel

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_run_workflow_rejects_unknown_set_piece_type(events):
    with pytest.raises(ValueError):
        run_workflow(events, "not_a_real_type")


def test_run_workflow_without_model_leaves_value_and_player_rating_none(events):
    result = run_workflow(events, "corner")
    assert isinstance(result, SetPieceWorkflow)
    assert result.added_value is None
    assert result.player_rating is None
    assert result.team_rating is not None
    assert "rating" in result.team_rating.columns


def test_run_workflow_with_model_populates_every_field_for_corner(events, model):
    result = run_workflow(events, "corner", model=model, min_deliveries=1, min_shots=1)
    assert result.set_piece_type == "corner"
    assert not result.summary.empty
    assert not result.team_counts.empty
    assert result.deliveries is not None
    assert result.second_phases is not None
    assert result.retention is not None
    assert result.added_value is not None
    assert not result.report.empty
    assert "rating" in result.team_rating.columns
    assert result.player_rating is not None


def test_run_workflow_penalty_has_no_deliveries_retention_or_second_phase(events):
    result = run_workflow(events, "penalty")
    assert result.deliveries is None
    assert result.retention is None
    assert result.second_phases is None


def test_run_workflow_throw_in_has_deliveries_and_retention_but_no_second_phase(events):
    result = run_workflow(events, "throw_in")
    assert result.deliveries is not None
    assert result.retention is not None
    assert result.second_phases is None  # only corner/free_kick get second-phase detection


def test_run_workflow_report_matches_direct_set_piece_report_call(events, model):
    from wa_setpieces.core.report import corner_report

    result = run_workflow(events, "corner", model=model)
    direct = corner_report(events, model=model)
    assert result.report.equals(direct)


def test_run_workflow_team_rating_matches_direct_rating_call(events, model):
    from wa_setpieces.core.rating import team_rating

    result = run_workflow(events, "corner", model=model)
    direct = team_rating(result.report)
    assert result.team_rating.equals(direct)
