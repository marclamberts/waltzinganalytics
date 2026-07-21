from pathlib import Path

import pytest

from wa_setpieces import load_events
from wa_setpieces.core.metrics import delivery_locations
from wa_setpieces.core.value import set_piece_added_value, set_piece_value_summary
from wa_setpieces.core.xt import XTModel

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def model(events):
    return XTModel.fit(events, x_bins=8, y_bins=6)


def test_added_value_one_row_per_delivery(events, model):
    detail = set_piece_added_value(events, "corner", model)
    assert len(detail) == len(delivery_locations(events, "corner"))
    assert {"delivery_xt_added", "shot_value", "added_value", "is_goal"}.issubset(detail.columns)


def test_added_value_has_no_nans(events, model):
    # Unlike set_piece_delivery_xt, added_value must always be summable --
    # an unsuccessful delivery still contributes 0, not NaN.
    detail = set_piece_added_value(events, "corner", model)
    assert detail["delivery_xt_added"].notna().all()
    assert detail["shot_value"].notna().all()
    assert detail["added_value"].notna().all()


def test_added_value_equals_sum_of_components(events, model):
    detail = set_piece_added_value(events, "free_kick", model)
    assert (
        detail["added_value"] == detail["delivery_xt_added"] + detail["shot_value"]
    ).all()


def test_added_value_zero_for_unsuccessful_delivery_with_no_shot(events, model):
    detail = set_piece_added_value(events, "corner", model)
    no_shot_unsuccessful = detail[(detail["outcome"] == 0) & (~detail["is_goal"])]
    # These may still have nonzero shot_value if a second-phase-linked shot
    # happened despite the delivery pass itself failing -- but delivery_xt
    # must be exactly 0 (not just close), since it's gated on outcome == 1.
    assert (no_shot_unsuccessful["delivery_xt_added"] == 0).all()


def test_shot_value_requires_fitted_model(events):
    from wa_setpieces.core.xt import XTModel
    import numpy as np

    loaded = XTModel(grid=np.zeros((6, 8)), x_bins=8, y_bins=6)
    with pytest.raises(ValueError):
        loaded.shot_value(50, 50)


def test_value_summary_matches_detail_totals(events, model):
    detail = set_piece_added_value(events, "corner", model)
    summary = set_piece_value_summary(events, "corner", model)
    assert summary["deliveries"].sum() == len(detail)
    assert summary["goals"].sum() == detail["is_goal"].sum()
    # total_added_value is rounded to 4dp in the summary, so compare loosely.
    assert summary["total_added_value"].sum() == pytest.approx(detail["added_value"].sum(), abs=1e-3)


def test_value_summary_empty_when_no_deliveries(model):
    import pandas as pd

    empty_events = pd.DataFrame(
        columns=[
            "id", "eventId", "typeId", "periodId", "timeMin", "timeSec",
            "contestantId", "playerId", "playerName", "outcome", "x", "y", "timeStamp",
        ]
    )
    summary = set_piece_value_summary(empty_events, "corner", model)
    assert summary.empty
    assert list(summary.columns) == [
        "contestantId", "deliveries", "total_added_value", "avg_added_value", "goals"
    ]
