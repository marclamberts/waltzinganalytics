"""Load Opta F24 JSON event feeds into a flat :class:`pandas.DataFrame`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class Match:
    """A parsed Opta F24 match export.

    ``match_details`` holds the raw ``matchDetails`` block (periods, scores,
    ...). ``events`` has one row per event and one column per distinct
    ``qualifierId`` plus the core event fields (``id``, ``eventId``,
    ``typeId``, ``periodId``, ``timeMin``, ``timeSec``, ``contestantId``,
    ``playerId``, ``playerName``, ``outcome``, ``x``, ``y``). Qualifier
    columns are named ``q_<qualifierId>`` and hold the qualifier's string
    ``value`` (or ``True`` for boolean-style qualifiers that carry no value).
    """

    match_details: dict[str, Any]
    events: pd.DataFrame


def _qualifier_columns(qualifiers: list[dict[str, Any]]) -> dict[str, Any]:
    cols: dict[str, Any] = {}
    for q in qualifiers:
        qid = q["qualifierId"]
        cols[f"q_{qid}"] = q.get("value", True)
    return cols


_CORE_FIELDS = (
    "id",
    "eventId",
    "typeId",
    "periodId",
    "timeMin",
    "timeSec",
    "contestantId",
    "playerId",
    "playerName",
    "outcome",
    "x",
    "y",
    "timeStamp",
)


def load_events(source: str | Path | dict) -> Match:
    """Parse an Opta F24 JSON export (path or already-loaded dict).

    Args:
        source: Path to a ``.json`` file, or a dict already produced by
            ``json.load`` on an F24 export.

    Returns:
        A :class:`Match` with a tidy events DataFrame, sorted by match time.
    """
    if isinstance(source, dict):
        data = source
    else:
        path = Path(source)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

    raw_events = data.get("event", [])
    rows = []
    for e in raw_events:
        row = {field: e.get(field) for field in _CORE_FIELDS}
        row.update(_qualifier_columns(e.get("qualifier", [])))
        rows.append(row)

    events = pd.DataFrame(rows)
    if not events.empty:
        events = events.sort_values(
            ["periodId", "timeMin", "timeSec", "eventId"]
        ).reset_index(drop=True)

    return Match(match_details=data.get("matchDetails", {}), events=events)
