"""Load Opta JSON event feeds into a flat :class:`pandas.DataFrame`."""

from __future__ import annotations

import json
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

_PROVIDERS = ("opta", "statsbomb", "impect")


@dataclass(frozen=True)
class Match:
    """A parsed Opta match export.

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
    """Parse an Opta JSON export (path or already-loaded dict).

    Args:
        source: Path to a ``.json`` file, or a dict already produced by
            ``json.load`` on an Opta export.

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
        # eventId is only unique within one team's own stream (see the
        # "By metric" docs page's "Linking to shots and goals" entry), so
        # it can't reliably break ties between
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
    """Load and concatenate several Opta match exports into one events DataFrame.

    Each source is parsed with :func:`load_events`, then stacked with a new
    ``matchId`` column so rows stay attributable to their match (the feed itself
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


_TYPES = ("match", "season")
_SEASON_EXTENSIONS = (".json", ".csv")


def _resolve_provider_files(source: str | Path, type_key: str) -> list[Path]:
    """Which file(s) to read for ``type_key`` -- independent of
    ``provider``: any provider's data can arrive as ``.json`` or
    ``.csv``, so this never gates on one fixed extension per provider.
    Whether a given file actually parses under the chosen provider is
    for the provider's own loader to decide (and, for ``type="season"``,
    for :func:`load_matches` to skip with a warning if it doesn't --
    see its docstring)."""
    path = Path(source)
    if type_key == "season":
        if path.is_file():
            raise ValueError(
                f"type='season' expects a directory of files, got a single file: {path} "
                "-- pass type='match' to load just this one."
            )
        if not path.is_dir():
            raise FileNotFoundError(str(path))
        files = sorted(
            p for ext in _SEASON_EXTENSIONS for p in path.glob(f"*{ext}")
        )
        if not files:
            raise FileNotFoundError(
                f"no {'/'.join(_SEASON_EXTENSIONS)} files found in directory {path}"
            )
        return files
    # type == "match"
    if path.is_dir():
        raise ValueError(
            f"type='match' expects a single file, got a directory: {path} -- pass "
            "type='season' to load every file in it."
        )
    if not path.exists():
        raise FileNotFoundError(str(path))
    return [path]


def load_matches(source: str | Path, provider: str = "opta", type: str = "match") -> pd.DataFrame:
    """Load a match export into a combined events DataFrame -- the same
    shape :func:`load_events_multi` produces, with a ``matchId`` column,
    ready for :class:`~wa_setpieces.core.season.SeasonDataset` or any
    match-safe function in this package.

    This is the one entry point for loading data regardless of where it
    came from or how much of it there is: every call has the same two
    knobs, ``provider`` and ``type``, and nothing else about the call
    changes shape between them --

    .. code-block:: python

       load_matches("match.json", provider="opta", type="match")
       load_matches("season/", provider="statsbomb", type="season")
       load_matches("impect_export.csv", provider="impect", type="match")

    The actual format-specific parsing still lives in
    :mod:`wa_setpieces.core.loader` (Opta) and :mod:`wa_setpieces.providers`
    (StatsBomb, IMPECT) -- this function only resolves *which* files to
    read for the declared ``type`` and dispatches to the right one.

    Args:
        source: for ``type="match"``, a single match file -- any
            provider can be ``.json`` or ``.csv``; the extension is never
            what decides how it's parsed, ``provider`` is. For
            ``type="season"``, a directory containing several -- scanned
            non-recursively for every ``*.json`` and ``*.csv`` file in
            it together (same reasoning: not gated to one extension per
            provider), sorted by filename. Passing a directory with
            ``type="match"`` (or a file with ``type="season"``) raises
            ``ValueError`` rather than silently doing the other thing.
        provider: ``"opta"`` (default), ``"statsbomb"`` or ``"impect"``,
            case-insensitive. Determines how a file's *content* is
            parsed, independent of its extension.
        type: ``"match"`` (default) for a single file, ``"season"`` for a
            directory of them, case-insensitive. IMPECT is the one
            partial exception worth knowing about: a single
            ``type="match"`` IMPECT export commonly covers many matches
            *already* (its own ``match_id`` column), unlike Opta/
            StatsBomb's true one-file-one-match convention -- see
            :mod:`wa_setpieces.providers.impect`'s module docstring.

    Returns:
        One combined events DataFrame with a ``matchId`` column. For
        ``"opta"``/``"statsbomb"`` each file is one match, tagged with its
        filename stem (same convention as :func:`load_events_multi`). For
        ``"impect"``, ``matchId`` comes from the export's own ``match_id``
        column instead.

    A ``type="season"`` folder scan matches every ``.json``/``.csv`` file
    regardless of provider, but a real export directory can also contain
    non-event sidecar files of the same extension (a StatsBomb
    ``matches.json``/``competitions.json`` sitting next to the per-match
    event files, say) or files for a different provider entirely. A file
    that doesn't parse as a valid match export for the chosen
    ``provider`` is skipped with a :class:`UserWarning` naming it and
    why, rather than either silently corrupting the combined frame or
    aborting the whole folder over one bad file.

    Raises:
        ValueError: ``type`` isn't ``"match"``/``"season"``, or doesn't
            match what ``source`` actually is (see ``source`` above); or
            two different files resolve to the same ``matchId`` -- see
            :func:`load_events_multi` for why this fails loudly rather
            than silently merging; or *every* file for this provider
            failed to parse.
        FileNotFoundError: ``source`` doesn't exist, or (for
            ``type="season"``) is a directory with no ``.json``/``.csv``
            files in it at all.
    """
    provider_key = provider.lower()
    if provider_key not in _PROVIDERS:
        raise ValueError(f"provider must be one of {_PROVIDERS}, got {provider!r}")
    type_key = type.lower()
    if type_key not in _TYPES:
        raise ValueError(f"type must be one of {_TYPES}, got {type!r}")
    files = _resolve_provider_files(source, type_key)

    frames: list[pd.DataFrame] = []
    match_id_sources: dict[str, Path] = {}

    def _claim(match_id: str, origin: Path) -> None:
        if match_id in match_id_sources:
            raise ValueError(
                f"duplicate matchId {match_id!r} from {match_id_sources[match_id]} and "
                f"{origin} would silently merge distinct matches -- rename one of the "
                "files, or pre-filter the folder."
            )
        match_id_sources[match_id] = origin

    skipped: list[tuple[Path, str]] = []

    if provider_key == "opta":
        for file in files:
            try:
                df = load_events(file).events.copy()
            except (ValueError, KeyError) as exc:
                skipped.append((file, str(exc)))
                continue
            match_id = file.stem
            _claim(match_id, file)
            df.insert(0, "matchId", match_id)
            frames.append(df)
    elif provider_key == "statsbomb":
        from ..providers.statsbomb import load_statsbomb_events

        for file in files:
            try:
                df = load_statsbomb_events(file).copy()
            except (ValueError, KeyError) as exc:
                skipped.append((file, str(exc)))
                continue
            match_id = file.stem
            _claim(match_id, file)
            df.insert(0, "matchId", match_id)
            frames.append(df)
    else:  # impect
        from ..providers.impect import load_impect_events

        for file in files:
            try:
                df = load_impect_events(file)
            except (ValueError, KeyError) as exc:
                skipped.append((file, str(exc)))
                continue
            for match_id in df["matchId"].drop_duplicates():
                _claim(match_id, file)
            frames.append(df)

    if skipped:
        # A folder scan matches every file with the right extension, but a
        # real export directory commonly has non-event sidecar files too
        # (a StatsBomb matches.json/competitions.json next to the per-match
        # event files, say) -- caught in practice on a real season folder,
        # where matches.json silently produced 242 garbage rows before
        # providers.statsbomb validated its input shape. Skipped loudly
        # (a warning, not silence) rather than aborting the whole folder.
        for file, reason in skipped:
            warnings.warn(
                f"load_matches: skipped {file} -- {reason}", stacklevel=2
            )
        if len(skipped) == len(files):
            raise ValueError(
                f"None of the {len(files)} file(s) for provider={provider!r} could be "
                f"loaded. First error: {skipped[0][1]}"
            )

    if not frames:
        return pd.DataFrame(columns=["matchId", *_CORE_FIELDS])
    return pd.concat(frames, ignore_index=True)
