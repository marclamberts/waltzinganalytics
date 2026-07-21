"""Convert Opta F24 event exports into a flat "corners" table.

Turns a directory of per-match F24 JSON exports plus a companion match-list
CSV into one row per corner delivery -- taker, delivery zone/technique, and
(if the corner produced a shot within a short time/possession window) the
resulting shot's outcome and xG. This is a different, denormalized schema
from :func:`wa_setpieces.core.loader.load_events`'s tidy per-event frame:
it is meant to match external "<competition> - Corners <season>.parquet"
exports (StatsBomb-style column names) that other tools already consume, so
this dataset can be produced for a new competition without changing those
tools.

Match-list CSV columns used (a standard Opta ``matchInfo`` export, one row
per match):

.. code-block:: text

    matchInfo/id                    Opta match ID (alphanumeric)
    matchInfo/localDate             match date (YYYY-MM-DD)
    matchInfo/contestant/0/id       contestant A ID
    matchInfo/contestant/0/name     contestant A name
    matchInfo/contestant/0/position "home" / "away"
    matchInfo/contestant/1/id       contestant B ID
    matchInfo/contestant/1/name     contestant B name
    matchInfo/contestant/1/position "home" / "away"

Each ``<date>...json`` F24 export is matched to a match-list row by (date,
{contestantId set}) rather than fuzzy name matching, since the match-list's
contestant IDs are exactly the ``contestantId`` values used in the event
JSON.

Beyond the set-piece qualifiers already in :mod:`wa_setpieces.core.constants`
(corner qualifier, pass end x/y, delivery zone), this module reads a few
qualifiers specific to describing a delivery's *outcome*: qualifier 103
(xG, percentage string), 22 (headed), 82 (blocked, on Attempt Saved
events), and 72/224 (inswinging/outswinging corner).
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import pandas as pd

from ..core import constants as c
from ..core.loader import load_events

Q_XG = 103
Q_HEADED = 22
Q_BLOCKED = 82
Q_INSWING = 72
Q_OUTSWING = 224

# Event typeIds that break a running possession (out of play, sub, card,
# formation change, ...) -- a new possession always starts after one of these.
BREAK_TYPE_IDS = frozenset({30, 32, 34, 37, 40, 42, 68, 70})

SHOT_WINDOW_DEFAULT = 30  # seconds after a corner to look for a linked shot

_OUTPUT_COLUMNS = (
    "match_id", "Match", "possession", "pass_timestamp", "pass_team_name",
    "Taker", "pass_position", "pass.height.name", "pass.body_part.name",
    "pass.outcome.name", "pass.technique.name", "pass_location_x",
    "pass_location_y", "pass_end_location_x", "pass_end_location_y",
    "shot_timestamp", "shot_team_name", "Shooter", "shot_position",
    "shot.body_part.name", "shot.outcome.name", "shot.statsbomb_xg",
    "shot_location_x", "shot_location_y", "shot_location_z",
    "Defensive_setup", "Minute", "Second", "SP_outcome",
)


# -- Per-row qualifier helpers (operate on a `load_events` events row) -------

def get_q(row: pd.Series, qualifier_id: int, default=None):
    val = row.get(f"q_{qualifier_id}")
    return val if pd.notna(val) else default


def has_q(row: pd.Series, qualifier_id: int) -> bool:
    return pd.notna(row.get(f"q_{qualifier_id}"))


def _opta_id_to_int(opta_id: str) -> int:
    """Deterministically fold an alphanumeric Opta match ID into an int64."""
    return zlib.crc32(opta_id.encode()) & 0x7FFFFFFF


def _xg(row: pd.Series):
    raw = get_q(row, Q_XG)
    if raw is None:
        return None
    try:
        return round(float(raw) / 100.0, 4)
    except (ValueError, TypeError):
        return None


def _to_sb_x(v):
    return round(float(v) * 1.2, 1) if v is not None and pd.notna(v) else None


def _to_sb_y(v):
    return round(float(v) * 0.8, 1) if v is not None and pd.notna(v) else None


def _technique(row: pd.Series):
    if has_q(row, Q_INSWING):
        return "Inswinging"
    if has_q(row, Q_OUTSWING):
        return "Outswinging"
    return None


def _pass_outcome(row: pd.Series):
    return None if row.get("outcome", 1) == 1 else "Incomplete"


def _shot_outcome(row: pd.Series):
    t = row.get("typeId")
    if t == c.TYPE_GOAL:
        return "Goal"
    if t == c.TYPE_POST:
        return "Post"
    if t == c.TYPE_MISS:
        return "Off T"
    if t == c.TYPE_ATTEMPT_SAVED:
        return "Blocked" if has_q(row, Q_BLOCKED) else "Saved"
    return None


def _body_part(row: pd.Series):
    return "Head" if has_q(row, Q_HEADED) else "Right Foot"


def _secs(row: pd.Series) -> int:
    minute = row.get("timeMin") or 0
    second = row.get("timeSec") or 0
    return int(minute) * 60 + int(second)


# -- Match-list CSV -> lookup by (date, contestant id set) ------------------

def load_match_list(matches_csv: str | Path) -> dict[str, list[dict]]:
    """Read a match-list CSV into ``{date: [record, ...]}``.

    Each record has ``match_id`` (int64, folded from the Opta match ID),
    ``home_id``/``home_name``/``away_id``/``away_name``, and ``ids`` -- the
    frozenset of both contestant IDs, used to disambiguate same-day matches.
    """
    df = pd.read_csv(matches_csv, dtype=str)
    df.columns = [col.strip() for col in df.columns]

    by_date: dict[str, list[dict]] = {}
    for _, row in df.iterrows():
        opta_id = str(row.get("matchInfo/id", "")).strip()
        date = str(row.get("matchInfo/localDate", "")).strip()[:10]
        c0_id = str(row.get("matchInfo/contestant/0/id", "")).strip()
        c1_id = str(row.get("matchInfo/contestant/1/id", "")).strip()
        c0_name = str(row.get("matchInfo/contestant/0/name", "")).strip()
        c1_name = str(row.get("matchInfo/contestant/1/name", "")).strip()
        c0_pos = str(row.get("matchInfo/contestant/0/position", "")).strip()
        if not opta_id or not c0_id or not c1_id:
            continue

        if c0_pos == "home":
            home_id, home_name, away_id, away_name = c0_id, c0_name, c1_id, c1_name
        else:
            home_id, home_name, away_id, away_name = c1_id, c1_name, c0_id, c0_name

        by_date.setdefault(date, []).append({
            "match_id": _opta_id_to_int(opta_id),
            "home_id": home_id,
            "away_id": away_id,
            "home_name": home_name,
            "away_name": away_name,
            "ids": frozenset({c0_id, c1_id}),
        })
    return by_date


def match_record(date: str, ids: frozenset, by_date: dict[str, list[dict]]) -> dict | None:
    for rec in by_date.get(date, []):
        if rec["ids"] == ids:
            return rec
    return None


# -- Possession tracker -------------------------------------------------------

def build_possessions(events: pd.DataFrame) -> list[int]:
    """One running possession number per row, incrementing on a team change
    or a break-type event (sub, card, out of play, ...)."""
    poss_num = 0
    last_team = None
    out = []
    for team, type_id in zip(events["contestantId"], events["typeId"]):
        if type_id in BREAK_TYPE_IDS or pd.isna(team):
            poss_num += 1
            last_team = None
        elif team != last_team and last_team is not None:
            poss_num += 1
            last_team = team
        else:
            last_team = team
        out.append(poss_num)
    return out


def find_linked_shot(
    events: pd.DataFrame,
    sp_index: int,
    sp_poss: int,
    possessions: list[int],
    shot_window: int,
) -> pd.Series | None:
    """The first shot by the corner-taking team within ``shot_window``
    seconds and at most one possession past the corner, or ``None``."""
    sp_row = events.iloc[sp_index]
    sp_secs = _secs(sp_row)
    sp_period = sp_row.get("periodId")
    sp_team = sp_row.get("contestantId")

    for i in range(sp_index + 1, len(events)):
        row = events.iloc[i]
        if row.get("periodId") != sp_period:
            break
        if _secs(row) - sp_secs > shot_window:
            break
        if (
            row.get("typeId") in c.SHOT_TYPE_IDS
            and row.get("contestantId") == sp_team
            and possessions[i] <= sp_poss + 1
        ):
            return row
    return None


# -- Build corner rows for one match -----------------------------------------

def corner_rows_for_match(
    events: pd.DataFrame,
    team_map: dict[str, str],
    match_id: int,
    label: str,
    *,
    shot_window: int = SHOT_WINDOW_DEFAULT,
) -> list[dict]:
    """One row per corner delivery in ``events`` (a :func:`load_events`
    frame for a single match), linking a shot if one follows within
    ``shot_window`` seconds."""
    poss = build_possessions(events)
    rows = []

    for i in range(len(events)):
        ev = events.iloc[i]
        if ev.get("typeId") != c.TYPE_PASS or not has_q(ev, c.QUALIFIER_CORNER_TAKEN):
            continue

        shot = find_linked_shot(events, i, poss[i], poss, shot_window)
        shot_delta = (_secs(shot) - _secs(ev)) if shot is not None else None
        if shot is None:
            sp_outcome = "No first contact - no shot"
        elif shot_delta is not None and shot_delta <= 3:
            sp_outcome = "First contact - shot within 3 seconds"
        else:
            sp_outcome = "No first contact - shot"

        rows.append({
            "match_id": match_id,
            "Match": label,
            "possession": poss[i],
            "pass_timestamp": f"{int(ev.get('timeMin') or 0):02d}:{int(ev.get('timeSec') or 0):02d}",
            "pass_team_name": team_map.get(ev.get("contestantId"), ""),
            "Taker": ev.get("playerName"),
            "pass_position": get_q(ev, c.QUALIFIER_ZONE) or "",
            "pass.height.name": "High Pass",
            "pass.body_part.name": _body_part(ev),
            "pass.outcome.name": _pass_outcome(ev),
            "pass.technique.name": _technique(ev),
            "pass_location_x": _to_sb_x(ev.get("x")),
            "pass_location_y": _to_sb_y(ev.get("y")),
            "pass_end_location_x": _to_sb_x(get_q(ev, c.QUALIFIER_PASS_END_X)),
            "pass_end_location_y": _to_sb_y(get_q(ev, c.QUALIFIER_PASS_END_Y)),
            "shot_timestamp": (
                f"{int(shot.get('timeMin') or 0):02d}:{int(shot.get('timeSec') or 0):02d}"
                if shot is not None else None
            ),
            "shot_team_name": (team_map.get(shot.get("contestantId"), "") if shot is not None else None),
            "Shooter": (shot.get("playerName") if shot is not None else None),
            "shot_position": (get_q(shot, c.QUALIFIER_ZONE) if shot is not None else None),
            "shot.body_part.name": (_body_part(shot) if shot is not None else None),
            "shot.outcome.name": (_shot_outcome(shot) if shot is not None else None),
            "shot.statsbomb_xg": (_xg(shot) if shot is not None else None),
            "shot_location_x": (_to_sb_x(shot.get("x")) if shot is not None else None),
            "shot_location_y": (_to_sb_y(shot.get("y")) if shot is not None else None),
            "shot_location_z": None,
            "Defensive_setup": "",
            "Minute": ev.get("timeMin"),
            "Second": ev.get("timeSec"),
            "SP_outcome": sp_outcome,
        })

    return rows


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df["match_id"] = df["match_id"].astype("int64")
    df["possession"] = df["possession"].astype("int64")
    df["Minute"] = pd.array(df["Minute"].values, dtype=pd.Int64Dtype())
    df["Second"] = pd.array(df["Second"].values, dtype=pd.Int64Dtype())
    for col in (
        "pass_location_x", "pass_location_y", "pass_end_location_x", "pass_end_location_y",
        "shot_location_x", "shot_location_y", "shot_location_z", "shot.statsbomb_xg",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# -- Batch driver --------------------------------------------------------------

def build_corners_dataset(
    events_dir: str | Path,
    matches_csv: str | Path,
    *,
    glob_pattern: str = "*.json",
    shot_window: int = SHOT_WINDOW_DEFAULT,
    verbose: bool = True,
) -> pd.DataFrame:
    """Convert every ``<date>...json`` F24 export in ``events_dir`` -- matched
    to a row in ``matches_csv`` by (date, contestant ID set) -- into one
    combined corners table.

    Files with no matching ``matches_csv`` row are skipped (reported when
    ``verbose``); this is the common case for exports outside the date/
    competition the CSV covers.
    """
    by_date = load_match_list(matches_csv)
    paths = sorted(Path(events_dir).glob(glob_pattern))

    rows: list[dict] = []
    skipped: list[str] = []
    for path in paths:
        date = path.stem[:10]
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        events = data.get("event", [])
        if not events:
            continue

        ids = frozenset(e["contestantId"] for e in events if "contestantId" in e)
        rec = match_record(date, ids, by_date)
        if rec is None:
            skipped.append(path.name)
            continue

        team_map = {rec["home_id"]: rec["home_name"], rec["away_id"]: rec["away_name"]}
        label = f"{rec['home_name']} - {rec['away_name']}"
        match_events = load_events(data).events
        rows.extend(corner_rows_for_match(
            match_events, team_map, rec["match_id"], label, shot_window=shot_window
        ))

    if verbose:
        print(f"  matched {len(paths) - len(skipped)} files, skipped {len(skipped)}")
        if skipped:
            print("  skipped files (no matching match-list row):")
            for name in skipped[:20]:
                print(f"    {name}")

    if not rows:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)
    return _coerce_dtypes(pd.DataFrame(rows))


def convert_to_parquet(
    events_dir: str | Path,
    matches_csv: str | Path,
    output_path: str | Path,
    *,
    glob_pattern: str = "*.json",
    shot_window: int = SHOT_WINDOW_DEFAULT,
    verbose: bool = True,
) -> Path:
    """Build the corners dataset and write it to ``output_path`` as parquet."""
    df = build_corners_dataset(
        events_dir, matches_csv,
        glob_pattern=glob_pattern, shot_window=shot_window, verbose=verbose,
    )
    output_path = Path(output_path)
    df.to_parquet(output_path, engine="pyarrow", compression="zstd", index=False)
    if verbose:
        print(f"  {len(df)} rows, {df['match_id'].nunique()} matches")
        print(f"Wrote {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wa-setpieces-convert-corners",
        description=(
            "Convert a directory of Opta F24 match JSON exports, plus a "
            "match-list CSV, into a flat corners parquet."
        ),
    )
    parser.add_argument("events_dir", help="Directory of <date>...json F24 exports")
    parser.add_argument("matches_csv", help="Match-list CSV (matchInfo/... columns)")
    parser.add_argument("output", help="Output .parquet path")
    parser.add_argument("--glob", default="*.json", help="Event file glob (default: *.json)")
    parser.add_argument(
        "--shot-window", type=int, default=SHOT_WINDOW_DEFAULT,
        help=f"Seconds after a corner to look for a linked shot (default: {SHOT_WINDOW_DEFAULT})",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args(argv)

    convert_to_parquet(
        args.events_dir, args.matches_csv, args.output,
        glob_pattern=args.glob, shot_window=args.shot_window, verbose=not args.quiet,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
