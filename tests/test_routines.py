from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import (
    SeasonDataset,
    all_routine_summaries,
    analyze_routines,
    load_events,
    restart_routines,
    routine_summary,
)
from wa_setpieces.core.routines import cluster_routines, cluster_summary

DATA = Path(__file__).parent / "data" / "sample_match.json"


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


@pytest.mark.parametrize("kind", ["corner", "free_kick", "throw_in", "goal_kick", "kick_off"])
def test_restart_routines_have_geometry_and_taxonomy(events, kind):
    detail = restart_routines(events, kind)
    assert not detail.empty
    assert {"routine_type", "distance", "progression", "direction", "target_channel", "retained"}.issubset(detail)
    assert detail["routine_type"].notna().all()


def test_corner_routine_categories_match_known_sample(events):
    detail = restart_routines(events, "corner")
    assert len(detail) == 9
    assert "short" in set(detail["routine_type"])
    assert detail["distance"].ge(0).all()


def test_routine_summary_usage_sums_to_one_per_team(events):
    summary = routine_summary(events, "free_kick")
    assert summary.groupby("contestantId")["usage_share"].sum().between(0.999, 1.001).all()
    assert summary["success_rate"].between(0, 1).all()


def test_routine_channel_and_side_match_zones_convention(events):
    # Regression test: routines.py used to define its own private
    # third/channel thresholds with the opposite left/right direction from
    # zones.add_channels' canonical convention (low y = left), so the same
    # delivery could get contradictory flank labels depending on which
    # function was called. It now reuses zones.add_thirds/add_channels
    # directly, so start_channel must agree with add_channels on the same
    # rows, and side/start_channel must agree with each other.
    from wa_setpieces.core.filters import extract_corners
    from wa_setpieces.core.zones import add_channels

    corners = extract_corners(events)
    direct = add_channels(corners, n=5).set_index("eventId")["channel"]
    detail = restart_routines(events, "corner").set_index("eventId")
    assert (detail["start_channel"].astype(str) == direct.loc[detail.index].astype(str)).all()

    low_y = detail["y"] < 40
    assert (detail.loc[low_y, "side"] == "left").all()
    assert (detail.loc[low_y, "start_channel"].isin(["left_wide", "left_half_space"])).all()
    high_y = detail["y"] > 60
    assert (detail.loc[high_y, "side"] == "right").all()
    assert (detail.loc[high_y, "start_channel"].isin(["right_wide", "right_half_space"])).all()


def test_penalty_taxonomy():
    base = {"id": 1, "eventId": 1, "periodId": 1, "timeMin": 10, "timeSec": 0,
            "contestantId": "A", "playerId": "p", "playerName": "Player", "outcome": 1,
            "x": 88.5, "y": 50.0, "timeStamp": None, "q_9": True}
    rows = [{**base, "eventId": i, "typeId": type_id} for i, type_id in enumerate((16, 15, 14, 13), 1)]
    detail = restart_routines(pd.DataFrame(rows), "penalty")
    assert detail["routine_type"].tolist() == ["scored", "saved", "post", "missed"]


def test_all_routine_summaries_contains_supported_sample_types(events):
    summary = all_routine_summaries(events)
    assert {"corner", "free_kick", "throw_in", "goal_kick", "kick_off"}.issubset(set(summary["set_piece_type"]))


def test_structured_analysis_contains_five_coordinated_tables(events):
    analysis = analyze_routines(events, "corner")
    assert analysis.set_piece_type == "corner"
    assert {"distance_m", "angle_degrees", "verticality", "destination_zone", "delivery_outcome", "routine_key"}.issubset(analysis.detail)
    assert {"routine_diversity", "top_pattern_share", "most_used_pattern"}.issubset(analysis.team_profiles)
    assert {"preferred_routine", "shots_created"}.issubset(analysis.taker_profiles)
    assert {"destination_zone", "team_usage_share"}.issubset(analysis.target_matrix)


def test_multi_match_routines_are_analysed_within_boundaries():
    season = SeasonDataset.from_sources([DATA, DATA], match_ids=["m1", "m2"])
    detail = analyze_routines(season.events, "corner").detail
    assert len(detail) == 18
    assert set(detail["matchId"]) == {"m1", "m2"}


def test_delivery_technique_from_inswing_outswing_qualifiers(events):
    detail = restart_routines(events, "corner")
    assert set(detail["delivery_technique"].dropna()) <= {"inswinger", "outswinger"}
    # Cross-checked against the raw qualifiers (see test_convert_corners.py's
    # regression test for the same qualifierId verification): every corner
    # tagged with qualifier 223 is an inswinger, 224 an outswinger, and a
    # delivery can't be both.
    corners = events.loc[(events["typeId"] == 1) & events["q_6"].notna()]
    n_inswing = corners["q_223"].notna().sum() if "q_223" in corners else 0
    n_outswing = corners["q_224"].notna().sum() if "q_224" in corners else 0
    assert (detail["delivery_technique"] == "inswinger").sum() == n_inswing
    assert (detail["delivery_technique"] == "outswinger").sum() == n_outswing


def test_cluster_routines_groups_deliveries_by_geometry(events):
    pytest.importorskip("sklearn")
    clustered = cluster_routines(events, "corner", n_clusters=3, random_state=0)
    assert len(clustered) == len(restart_routines(events, "corner"))
    assert {"cluster", "cluster_label"}.issubset(clustered.columns)
    assert clustered["cluster"].between(0, 2).all()  # every corner has a full x/y/end_x/end_y
    assert clustered["cluster_label"].notna().all()

    summary = cluster_summary(clustered)
    assert summary["attempts"].sum() == len(clustered)
    assert {"success_rate", "shot_rate", "avg_distance", "avg_progression"}.issubset(summary.columns)


def test_cluster_routines_too_few_deliveries_leaves_unclustered(events):
    pytest.importorskip("sklearn")
    clustered = cluster_routines(events, "corner", n_clusters=50, random_state=0)
    assert (clustered["cluster"] == -1).all()
    assert clustered["cluster_label"].isna().all()


def test_cluster_routines_requires_ml_extra_without_sklearn(events, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sklearn.cluster":
            raise ImportError("no sklearn")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="ml"):
        cluster_routines(events, "corner")


def test_post_target_near_far_central(events):
    detail = restart_routines(events, "corner")
    assert set(detail["post_target"].dropna()) <= {"near_post", "far_post", "central"}
    # A corner taken from the near-zero-y side that ends up on the same
    # (low-y) side of the box is a near-post delivery; one that ends up
    # curling to the opposite (high-y) side is far-post.
    reached_box = detail[detail["end_x"] >= 83]
    for _, row in reached_box.iterrows():
        if 42 <= row["end_y"] <= 58:
            assert row["post_target"] == "central"
        elif (row["end_y"] < 50) == (row["y"] < 50):
            assert row["post_target"] == "near_post"
        else:
            assert row["post_target"] == "far_post"


def test_long_throw_taker_summary_only_includes_long_throws(events):
    from wa_setpieces.core.routines import long_throw_taker_summary

    all_throws = restart_routines(events, "throw_in")
    summary = long_throw_taker_summary(events, min_distance=25.0)
    assert summary["long_throws"].sum() == (all_throws["distance"] >= 25.0).sum()
    assert {"share_of_team_throws", "retention_rate", "shots_created", "goals_created"}.issubset(summary.columns)
    assert summary["share_of_team_throws"].between(0, 1).all()


def test_long_throw_taker_summary_empty_when_threshold_too_high(events):
    from wa_setpieces.core.routines import long_throw_taker_summary

    summary = long_throw_taker_summary(events, min_distance=1000.0)
    assert summary.empty
    assert list(summary.columns) == [
        "playerId", "playerName", "contestantId", "long_throws",
        "share_of_team_throws", "retention_rate", "shots_created", "goals_created",
    ]


def test_long_throw_second_phases_covers_only_long_deliveries(events):
    from wa_setpieces.core.routines import long_throw_second_phases

    all_throws = restart_routines(events, "throw_in")
    result = long_throw_second_phases(events, min_distance=25.0)
    assert len(result) == (all_throws["distance"] >= 25.0).sum()
    assert result["delivery_event_id"].isin(
        all_throws.loc[all_throws["distance"] >= 25.0, "eventId"]
    ).all()
    assert result["second_phase_shot"].isin([True, False]).all()


def test_long_throw_second_phases_empty_when_no_long_throws(events):
    from wa_setpieces.core.routines import long_throw_second_phases

    result = long_throw_second_phases(events, min_distance=1000.0)
    assert result.empty


def test_long_throw_second_phases_stays_within_match_boundaries():
    # Regression test: long_throw_second_phases built matchId-aware keys to
    # pick out long throws, but then handed classify_phase the *whole*
    # multi-match frame, which walks forward by raw position and only
    # breaks on a periodId change -- so a throw-in that is the last event
    # of match m1 would pick up the first event of match m2 (right after
    # it in the concatenated frame, same periodId, clock reset to ~0) as if
    # it were the very next event of its own match. Below, m1's long throw
    # has no real follow-up at all; m2's first event is an unrelated goal
    # 1 second later on the reset clock. Without per-match scoping this
    # throw-in is misreported as producing that goal as a direct shot.
    from wa_setpieces.core import constants as c
    from wa_setpieces.core.routines import long_throw_second_phases

    events = pd.DataFrame(
        [
            dict(
                matchId="m1", eventId=50, typeId=c.TYPE_PASS, periodId=1,
                timeMin=0, timeSec=0, contestantId="B", playerId="pB1",
                playerName="B1", outcome=1, x=50.0, y=50.0,
            ),
            dict(
                matchId="m1", eventId=1, typeId=c.TYPE_PASS, periodId=1,
                timeMin=0, timeSec=5, contestantId="A", playerId="pA1",
                playerName="A1", outcome=1, x=0.0, y=0.0,
                q_107=True, q_140=40.0, q_141=0.0,
            ),
            dict(
                matchId="m2", eventId=1, typeId=c.TYPE_GOAL, periodId=1,
                timeMin=0, timeSec=6, contestantId="A", playerId="pA2",
                playerName="A2", outcome=1, x=95.0, y=50.0,
            ),
            dict(
                matchId="m2", eventId=51, typeId=c.TYPE_PASS, periodId=1,
                timeMin=0, timeSec=0, contestantId="B", playerId="pB2",
                playerName="B2", outcome=1, x=50.0, y=50.0,
            ),
        ]
    )
    result = long_throw_second_phases(events, min_distance=25.0)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["direct_shot"] == False  # noqa: E712
    assert row["direct_shot_is_goal"] == False  # noqa: E712
    assert row["first_contact_event_id"] is None
