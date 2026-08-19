"""Load Opta F24 JSON event feeds into a flat :class:`pandas.DataFrame`."""

from __future__ import annotations

import json
from collections.abc import Sequence
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

    events = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(_CORE_FIELDS))
    if not events.empty:
        # eventId is only unique within one team's own stream (see
        # docs/source/advanced.rst), so it can't reliably break ties between
        # two teams' events in the same second. timeStamp carries
        # sub-second precision when the export provides it, so prefer it as
        # a finer-grained tiebreak; eventId remains the final fallback for
        # exports without it (or for genuine same-timestamp ties).
        sort_ts = pd.to_datetime(events.get("timeStamp"), errors="coerce")
        events = (
            events.assign(_sort_ts=sort_ts)
            .sort_values(
                ["periodId", "timeMin", "timeSec", "_sort_ts", "eventId"],
                na_position="last",
            )
            .drop(columns="_sort_ts")
            .reset_index(drop=True)
        )

    return Match(match_details=data.get("matchDetails", {}), events=events)


def load_events_multi(
    sources: Sequence[str | Path | dict],
    match_ids: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load and concatenate several F24 match exports into one events DataFrame.

    Each source is parsed with :func:`load_events`, then stacked with a new
    ``matchId`` column so rows stay attributable to their match (F24 itself
    carries no match identifier, and per-match ``eventId`` numbering restarts
    at 1, so without this column rows from different matches would collide).

    Args:
        sources: paths (or already-loaded dicts) for each match, in any order.
        match_ids: optional label per source. Defaults to the file's stem
            (``"2026-02-20_match"`` from ``2026-02-20_match.json``) for path
            sources, or the source's position for dict sources.

    Raises:
        ValueError: if two sources resolve to the same ``matchId`` (whether
            passed explicitly or derived from the file stem -- e.g. two
            different directories both containing a ``matchday3.json``).
            Every safety this module and :class:`~wa_setpieces.core.season.SeasonDataset`
            build on top of ``matchId`` being unique per match depends on
            this; silently merging two matches under one ID would defeat
            all of it, so this fails loudly instead.

    Returns:
        One combined events DataFrame, sorted within each match by time but
        with no relationship implied *between* matches.

    .. important::
       This is for **match-independent aggregation only** -- team/player
       set-piece counts, zone heatmaps, and fitting :meth:`XTModel.fit`
       across a season all work fine on the combined frame, since those
       operate row-by-row or via groupby. The temporal-window functions in
       :mod:`wa_setpieces.core.phases` and :mod:`wa_setpieces.core.retention` assume a
       single chronologically-ordered match, so feeding them this combined
       frame directly would let a window bleed across a match boundary.
       Run those per match (``for path in paths: ...``) and concatenate the
       *results* instead.
    """
    if match_ids is not None and len(match_ids) != len(sources):
        raise ValueError("match_ids must be the same length as sources")

    resolved_ids = []
    for i, source in enumerate(sources):
        if match_ids is not None:
            resolved_ids.append(match_ids[i])
        elif isinstance(source, dict):
            resolved_ids.append(str(i))
        else:
            resolved_ids.append(Path(source).stem)
    seen: dict[str, int] = {}
    duplicates = {}
    for i, match_id in enumerate(resolved_ids):
        if match_id in seen:
            duplicates.setdefault(match_id, [seen[match_id]]).append(i)
        else:
            seen[match_id] = i
    if duplicates:
        detail = "; ".join(
            f"{match_id!r} used by sources at positions {positions}"
            for match_id, positions in duplicates.items()
        )
        raise ValueError(
            f"duplicate matchId would silently merge distinct matches: {detail}. "
            "Pass explicit unique match_ids."
        )

    frames = []
    for match_id, source in zip(resolved_ids, sources):
        match = load_events(source)
        df = match.events.copy()
        df.insert(0, "matchId", match_id)
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["matchId", *_CORE_FIELDS])
    return pd.concat(frames, ignore_index=True)
