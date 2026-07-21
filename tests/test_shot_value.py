from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("xgboost")
pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from wa_setpieces import load_events  # noqa: E402
from wa_setpieces.ml.shot_value import (  # noqa: E402
    PONTARGET_FEATURES,
    SITUATION_FEATURES,
    XGOT_FEATURES,
    ShotValueModels,
    build_shot_features,
    shot_value,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.fixture(scope="module")
def models():
    return ShotValueModels.load()


def test_build_shot_features_one_row_per_shot(events):
    from wa_setpieces.core import constants as c

    feats = build_shot_features(events)
    n_shots = events["typeId"].isin(c.SHOT_TYPE_IDS).sum()
    assert len(feats) == n_shots


def test_build_shot_features_has_all_model_feature_columns(events):
    feats = build_shot_features(events)
    needed = set(PONTARGET_FEATURES) | set(XGOT_FEATURES) | set(SITUATION_FEATURES)
    assert needed.issubset(feats.columns)


def test_build_shot_features_distance_and_angle_are_positive(events):
    feats = build_shot_features(events)
    assert (feats["distance"] >= 0).all()
    assert (feats["angle"] >= 0).all()
    assert (feats["angle"] <= 180).all()


def test_build_shot_features_body_part_flags_are_mutually_exclusive(events):
    feats = build_shot_features(events)
    total = feats["is_right_foot"] + feats["is_left_foot"] + feats["is_other_body_part"]
    assert (total == 1).all()


def test_build_shot_features_set_piece_flags_agree_with_chains(events):
    from wa_setpieces.core.chains import link_set_piece_shots

    feats = build_shot_features(events)
    linked = link_set_piece_shots(events)
    merged = feats.merge(linked[["eventId", "contestantId", "set_piece_type"]],
                          on=["eventId", "contestantId"], suffixes=("", "_linked"))
    # pandas treats None == None as False (missing-value semantics), so
    # compare through a sentinel fill rather than `==` directly.
    left = merged["set_piece_type"].fillna("__none__")
    right = merged["set_piece_type_linked"].fillna("__none__")
    assert (left == right).all()
    corner_mask = merged["set_piece_type"] == "corner"
    assert (merged.loc[corner_mask, "is_from_corner"] == 1).all()
    open_play_mask = merged["set_piece_type"].isna()
    assert (merged.loc[open_play_mask, "is_open_play"] == 1).all()
    assert (merged.loc[open_play_mask, "is_set_piece"] == 0).all()


def test_build_shot_features_empty_events_returns_empty_frame():
    empty = pd.DataFrame(columns=["id", "eventId", "typeId", "periodId", "timeMin", "timeSec",
                                   "contestantId", "playerId", "playerName", "outcome", "x", "y"])
    feats = build_shot_features(empty)
    assert feats.empty


def test_shot_value_models_load():
    models = ShotValueModels.load()
    assert models.pontarget is not None
    assert models.xgot is not None
    assert models.psxg is not None
    assert models.situation is not None
    assert models.multi_outcome is not None


def test_shot_value_returns_one_row_per_shot(events, models):
    result = shot_value(events, models)
    feats = build_shot_features(events)
    assert len(result) == len(feats)


def test_shot_value_probabilities_are_in_unit_range(events, models):
    result = shot_value(events, models)
    for col in ["on_target_prob", "xgot", "psxg", "situational_prob", "shot_value"]:
        assert (result[col] >= 0).all(), col
        assert (result[col] <= 1).all(), col


def test_shot_value_outcome_class_probs_sum_to_one(events, models):
    result = shot_value(events, models)
    class_cols = [c for c in result.columns if c.startswith("outcome_class_")]
    assert len(class_cols) == 4
    totals = result[class_cols].sum(axis=1)
    assert (totals - 1.0).abs().max() < 1e-6


def test_shot_value_blended_score_matches_formula(events, models):
    result = shot_value(events, models)
    expected = (result["psxg"] + result["on_target_prob"] * result["xgot"]) / 2.0
    assert (result["shot_value"] - expected).abs().max() < 1e-9


def test_shot_value_loads_models_lazily_if_not_passed(events):
    result = shot_value(events)
    assert not result.empty


def test_shot_value_no_nan_in_output(events, models):
    result = shot_value(events, models)
    numeric_cols = [
        "on_target_prob", "xgot", "psxg", "situational_prob", "shot_value",
        "outcome_class_0", "outcome_class_1", "outcome_class_2", "outcome_class_3",
    ]
    assert not result[numeric_cols].isna().any().any()
