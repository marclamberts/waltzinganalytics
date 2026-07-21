import io
from pathlib import Path

import pandas as pd
import pytest

from wa_setpieces import load_events
from wa_setpieces.convert.corners import (
    build_corners_dataset,
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
