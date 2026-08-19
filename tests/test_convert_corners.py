import io
from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.convert.corners import (
    build_corners_dataset,
    build_possessions,
    corner_rows_for_match,
    load_match_list,
    match_record,
)

DATA = Path(__file__).parent / "data" / "sample_match.json"
DATE = "2026-02-24"
HOME_ID = "cxb4hqite921i36gwrezdts7c"
AWAY_ID = "f2yd0yzt0om6qhks9gbowu1d6"

MATCHES_CSV = f"""matchInfo/id,matchInfo/localDate,matchInfo/contestant/0/id,matchInfo/contestant/0/name,matchInfo/contestant/0/position,matchInfo/contestant/1/id,matchInfo/contestant/1/name,matchInfo/contestant/1/position
abc123,{DATE},{HOME_ID},Home FC,home,{AWAY_ID},Away FC,away
"""

TEAM_MAP = {HOME_ID: "Home FC", AWAY_ID: "Away FC"}


def _ev(**kwargs):
    """One synthetic `load_events`-shaped row (team A unless overridden)."""
    row = dict(
        eventId=1, typeId=1, periodId=1, timeMin=10, timeSec=0,
        contestantId="A", playerName="P", outcome=1, x=99.5, y=99.5,
    )
    row.update(kwargs)
    return row


def _frame(rows):
    return pd.DataFrame(rows)


def _rows(events):
    return corner_rows_for_match(events, {"A": "A FC", "B": "B FC"}, match_id=1, label="A - B")


@pytest.fixture(scope="module")
def events():
    return load_events(DATA).events


def test_load_match_list_indexes_by_date_and_contestant_ids():
    by_date = load_match_list(io.StringIO(MATCHES_CSV))
    assert DATE in by_date
    rec = by_date[DATE][0]
    assert rec["ids"] == frozenset({HOME_ID, AWAY_ID})
    assert rec["home_id"] == HOME_ID
    assert rec["away_name"] == "Away FC"


def test_match_record_looks_up_by_date_and_id_set():
    by_date = load_match_list(io.StringIO(MATCHES_CSV))
    rec = match_record(DATE, frozenset({HOME_ID, AWAY_ID}), by_date)
    assert rec is not None
    assert match_record(DATE, frozenset({"nope", "nada"}), by_date) is None
    assert match_record("1999-01-01", frozenset({HOME_ID, AWAY_ID}), by_date) is None


def test_corner_rows_for_match_returns_one_row_per_corner(events):
    team_map = {HOME_ID: "Home FC", AWAY_ID: "Away FC"}
    rows = corner_rows_for_match(events, team_map, match_id=42, label="Home FC - Away FC")

    n_corners = (
        (events["typeId"] == 1) & events["q_6"].notna()
    ).sum()
    assert len(rows) == n_corners
    assert n_corners > 0

    row = rows[0]
    assert row["match_id"] == 42
    assert row["Match"] == "Home FC - Away FC"
    assert row["pass_team_name"] in ("Home FC", "Away FC")
    assert row["SP_outcome"] in (
        "No first contact - no shot",
        "First contact - shot within 3 seconds",
        "No first contact - shot",
    )


def test_corner_technique_uses_inswinger_not_left_footed_qualifier(events):
    # Regression test: Q_INSWING was 72, which is actually "Left Footed"
    # (confirmed against the sample match: qualifier 72 also appears on
    # shot events, where swing direction is meaningless, and co-occurs
    # with both the real in-swing and out-swing qualifiers depending on
    # which foot the taker used -- not correlated with swing direction at
    # all). The real in-swinger qualifier is 223, confirmed mutually
    # exclusive with 224 (out-swinger) across every corner in the sample
    # match. Cross-check technique against the raw qualifiers directly.
    team_map = {HOME_ID: "Home FC", AWAY_ID: "Away FC"}
    rows = corner_rows_for_match(events, team_map, match_id=42, label="Home FC - Away FC")
    corners = events.loc[(events["typeId"] == 1) & events["q_6"].notna()].reset_index(drop=True)
    assert len(rows) == len(corners)
    for row, (_, corner) in zip(rows, corners.iterrows()):
        if pd.notna(corner.get("q_223")):
            assert row["pass.technique.name"] == "Inswinging"
        elif pd.notna(corner.get("q_224")):
            assert row["pass.technique.name"] == "Outswinging"
        else:
            assert row["pass.technique.name"] is None
    # eventId 786 has both q_224 (outswinger) and q_72 (left-footed) --
    # exactly the case the old Q_INSWING=72 bug mislabeled as "Inswinging".
    left_footed_outswinger = corners.loc[corners["eventId"] == 786].iloc[0]
    assert pd.notna(left_footed_outswinger.get("q_72"))
    assert pd.notna(left_footed_outswinger.get("q_224"))
    idx = corners.index[corners["eventId"] == 786][0]
    assert rows[idx]["pass.technique.name"] == "Outswinging"


def test_body_part_uses_head_qualifier_not_the_regular_play_qualifier(events):
    # Regression test (same family as the Q_INSWING=72 bug): Q_HEADED used
    # to be 22, which in Opta is "Regular play" (a shot *situation* flag),
    # not "Head" -- 15 is. In the sample match all 26 shots carry either
    # q_20 (right footed) or q_72 (left footed) and none carry q_15, i.e.
    # there is not a single header, yet 15 of them carry q_22. eventId 734
    # is one of them: q_22 *and* q_20, so it is a right-footed shot the old
    # mapping reported as "Head". eventId 611 carries q_72 and used to fall
    # through to the "Right Foot" default.
    rows = corner_rows_for_match(events, TEAM_MAP, match_id=42, label="Home FC - Away FC")
    by_shot = {r["shot_timestamp"]: r for r in rows if r["Shooter"] is not None}

    shot_734 = events.loc[events["eventId"] == 734].iloc[0]
    assert pd.notna(shot_734.get("q_22")) and pd.notna(shot_734.get("q_20"))
    assert by_shot["82:30"]["shot.body_part.name"] == "Right Foot"

    shot_611 = events.loc[events["eventId"] == 611].iloc[0]
    assert pd.notna(shot_611.get("q_72"))
    assert by_shot["68:11"]["shot.body_part.name"] == "Left Foot"

    # A left-footed corner taker likewise must not be reported as right-footed.
    corner_191 = events.loc[events["eventId"] == 191].iloc[0]
    assert pd.notna(corner_191.get("q_72"))
    assert rows[0]["pass.body_part.name"] == "Left Foot"


def test_head_and_other_body_part_qualifiers_map_to_their_own_names():
    headed = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=16, timeSec=5, q_15=True),
    ]))
    assert headed[0]["shot.body_part.name"] == "Head"

    other = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=16, timeSec=5, q_21=True),
    ]))
    assert other[0]["shot.body_part.name"] == "Other"


def test_shot_xg_is_empty_because_f24_carries_no_xg_qualifier(events):
    # Regression test: Q_XG used to be 103, which is the goal-mouth *z*
    # coordinate (wa_setpieces.core.placement.QUALIFIER_GOAL_MOUTH_Z reads
    # it as exactly that). eventId 734 is an off-target miss with q_103 =
    # "65.3", which the old mapping emitted as an xG of 0.653.
    shot_734 = events.loc[events["eventId"] == 734].iloc[0]
    assert shot_734["q_103"] == "65.3"

    rows = corner_rows_for_match(events, TEAM_MAP, match_id=42, label="Home FC - Away FC")
    assert all(r["shot.statsbomb_xg"] is None for r in rows)


def test_locations_rescale_to_statsbomb_pitch_with_the_y_axis_flipped(events):
    # Regression test: Opta's y origin is the bottom touchline and
    # StatsBomb's is the top one, so y must flip as well as rescale.
    # Without the flip every delivery landed in the mirror-image corner.
    # Cross-check against footedness: a right-footed in-swinger can only be
    # taken from the attacker's left corner, which is high y in Opta and
    # *low* y in StatsBomb.
    rows = corner_rows_for_match(events, TEAM_MAP, match_id=42, label="Home FC - Away FC")
    corners = events.loc[(events["typeId"] == 1) & events["q_6"].notna()].reset_index(drop=True)

    for row, (_, corner) in zip(rows, corners.iterrows()):
        assert row["pass_location_x"] == pytest.approx(round(corner["x"] * 1.2, 1))
        assert row["pass_location_y"] == pytest.approx(round(80.0 - corner["y"] * 0.8, 1))
        right_footed = pd.isna(corner.get("q_72"))
        if right_footed and pd.notna(corner.get("q_223")):
            assert row["pass_location_y"] < 40  # StatsBomb left corner
        if right_footed and pd.notna(corner.get("q_224")):
            assert row["pass_location_y"] > 40  # StatsBomb right corner


def test_corner_links_the_shot_it_produced_across_a_lone_defensive_touch(events):
    # Regression test: build_possessions used to start a new possession on
    # every team alternation, but Opta interleaves single defensive touches
    # into the attacking team's stream. eventId 610 (corner) is followed
    # 3s later by a lone opposition clearance and then, 4s after the
    # corner, by eventId 611 -- a shot by the corner-taking team. The
    # clearance pushed the shot two possessions past the corner, so
    # find_linked_shot's "at most one possession past" test rejected it and
    # *every* corner in the match came back unlinked.
    rows = corner_rows_for_match(events, TEAM_MAP, match_id=42, label="Home FC - Away FC")
    linked = [r for r in rows if r["Shooter"] is not None]
    assert [r["shot_timestamp"] for r in linked] == ["68:11", "82:30"]
    assert linked[0]["shot.outcome.name"] == "Saved"
    assert linked[1]["shot.outcome.name"] == "Off T"
    assert all(r["SP_outcome"] == "No first contact - shot" for r in linked)


def test_build_possessions_ignores_a_lone_opposition_touch():
    poss = build_possessions(_frame([
        _ev(contestantId="A"), _ev(contestantId="A"),
        _ev(contestantId="B"),  # single defensive touch -- same possession
        _ev(contestantId="A"), _ev(contestantId="A"),
    ]))
    assert poss == [0, 0, 0, 0, 0]


def test_build_possessions_increments_on_a_sustained_switch_and_on_breaks():
    poss = build_possessions(_frame([
        _ev(contestantId="A"),
        _ev(contestantId="B"), _ev(contestantId="B"),  # sustained -> switch
        _ev(contestantId="B", typeId=30),  # break type
        _ev(contestantId="B"),
    ]))
    assert poss == [0, 1, 1, 2, 2]


def test_shot_within_three_seconds_is_reported_as_first_contact():
    rows = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=16, timeSec=3),
    ]))
    assert rows[0]["SP_outcome"] == "First contact - shot within 3 seconds"
    assert rows[0]["shot.outcome.name"] == "Goal"


def test_shot_exactly_on_the_window_edge_links_but_one_second_later_does_not():
    on_edge = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=15, timeMin=10, timeSec=30),
    ]))
    assert on_edge[0]["Shooter"] is not None
    assert on_edge[0]["shot.outcome.name"] == "Saved"

    past_edge = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=15, timeMin=10, timeSec=31),
    ]))
    assert past_edge[0]["Shooter"] is None
    assert past_edge[0]["SP_outcome"] == "No first contact - no shot"


def test_blocked_attempt_and_post_map_to_their_own_outcome_names():
    blocked = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=15, timeSec=5, q_82=True),
    ]))
    assert blocked[0]["shot.outcome.name"] == "Blocked"

    post = _rows(_frame([
        _ev(eventId=1, q_6=True),
        _ev(eventId=2, typeId=14, timeSec=5),
    ]))
    assert post[0]["shot.outcome.name"] == "Post"


def test_shot_in_the_next_period_is_not_linked():
    rows = _rows(_frame([
        _ev(eventId=1, q_6=True, periodId=1, timeMin=45, timeSec=0),
        _ev(eventId=2, typeId=16, periodId=2, timeMin=45, timeSec=10),
    ]))
    assert rows[0]["Shooter"] is None


def test_unsuccessful_corner_is_reported_as_an_incomplete_pass():
    rows = _rows(_frame([_ev(eventId=1, q_6=True, outcome=0)]))
    assert rows[0]["pass.outcome.name"] == "Incomplete"
    assert _rows(_frame([_ev(eventId=1, q_6=True, outcome=1)]))[0]["pass.outcome.name"] is None


def test_load_match_list_handles_away_listed_first_and_skips_incomplete_rows():
    # Regression test for the blank-cell half: the row guard used to read
    # cells with str(), and a blank cell comes back from pandas as NaN even
    # under dtype=str, so it became the truthy "nan" -- the guard never
    # fired and an id-less row was kept as a match named "nan".
    csv = (
        "matchInfo/id,matchInfo/localDate,matchInfo/contestant/0/id,"
        "matchInfo/contestant/0/name,matchInfo/contestant/0/position,"
        "matchInfo/contestant/1/id,matchInfo/contestant/1/name,"
        "matchInfo/contestant/1/position\n"
        f"abc123,{DATE},{AWAY_ID},Away FC,away,{HOME_ID},Home FC,home\n"
        f"nope,{DATE},,No Ids FC,home,,Other FC,away\n"
    )
    by_date = load_match_list(io.StringIO(csv))
    assert len(by_date[DATE]) == 1  # the id-less row is dropped
    rec = by_date[DATE][0]
    assert rec["home_id"] == HOME_ID
    assert rec["home_name"] == "Home FC"
    assert rec["away_name"] == "Away FC"


def test_build_corners_dataset_skips_a_file_with_no_events_and_reports_progress(tmp_path, capsys):
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / f"{DATE}_sample.json").write_text(DATA.read_text())
    (events_dir / f"{DATE}_empty.json").write_text('{"event": []}')
    (events_dir / "1999-01-01_other.json").write_text(DATA.read_text())
    matches_csv = tmp_path / "matches.csv"
    matches_csv.write_text(MATCHES_CSV)

    df = build_corners_dataset(events_dir, matches_csv, verbose=True)

    out = capsys.readouterr().out
    assert "skipped 1" in out
    assert "1999-01-01_other.json" in out
    assert set(df["Match"]) == {"Home FC - Away FC"}


def test_build_corners_dataset_matches_file_to_csv_row_by_date_and_ids(tmp_path):
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / f"{DATE}_sample.json").write_text(DATA.read_text())
    matches_csv = tmp_path / "matches.csv"
    matches_csv.write_text(MATCHES_CSV)

    df = build_corners_dataset(events_dir, matches_csv, verbose=False)

    assert not df.empty
    assert set(df["Match"]) == {"Home FC - Away FC"}
    assert df["match_id"].dtype == "int64"
    assert df["possession"].dtype == "int64"


def test_build_corners_dataset_skips_unmatched_files(tmp_path):
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "1999-01-01_sample.json").write_text(DATA.read_text())
    matches_csv = tmp_path / "matches.csv"
    matches_csv.write_text(MATCHES_CSV)

    df = build_corners_dataset(events_dir, matches_csv, verbose=False)

    assert df.empty
    assert list(df.columns)  # still has the expected schema, just no rows


def test_convert_to_parquet_writes_file(tmp_path):
    pytest.importorskip("pyarrow")
    from wa_setpieces.convert.corners import convert_to_parquet

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / f"{DATE}_sample.json").write_text(DATA.read_text())
    matches_csv = tmp_path / "matches.csv"
    matches_csv.write_text(MATCHES_CSV)
    output = tmp_path / "corners.parquet"

    convert_to_parquet(events_dir, matches_csv, output, verbose=False)

    assert output.exists()
    df = pd.read_parquet(output)
    assert not df.empty


def test_cli_main_writes_the_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    from wa_setpieces.convert.corners import main

    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / f"{DATE}_sample.json").write_text(DATA.read_text())
    matches_csv = tmp_path / "matches.csv"
    matches_csv.write_text(MATCHES_CSV)
    output = tmp_path / "corners.parquet"

    rc = main([str(events_dir), str(matches_csv), str(output), "--shot-window", "10", "--quiet"])

    assert rc == 0
    assert not pd.read_parquet(output).empty
