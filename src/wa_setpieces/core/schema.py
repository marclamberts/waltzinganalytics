"""Validation and capability discovery for provider-neutral event frames."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = (
    "eventId", "typeId", "periodId", "timeMin", "timeSec",
    "contestantId", "outcome", "x", "y",
)
OPTIONAL_COLUMNS = ("id", "playerId", "playerName", "timeStamp", "matchId")


class EventSchemaError(ValueError):
    """Raised when an event frame cannot safely be analysed."""


@dataclass(frozen=True)
class EventCapabilities:
    end_locations: bool
    assist_links: bool
    player_identity: bool
    match_identity: bool


def event_capabilities(events: pd.DataFrame) -> EventCapabilities:
    return EventCapabilities(
        end_locations={"q_140", "q_141"}.issubset(events.columns),
        assist_links="q_55" in events.columns,
        player_identity={"playerId", "playerName"}.issubset(events.columns),
        match_identity="matchId" in events.columns,
    )


def validate_events(events: pd.DataFrame, *, require_match_id: bool = False) -> pd.DataFrame:
    """Validate the shared event contract and return ``events`` unchanged.

    The function deliberately does not coerce caller data. Error messages
    identify missing fields and invalid coordinate/time values so adapters can
    be fixed at their boundary instead of allowing misleading downstream data.
    """
    if not isinstance(events, pd.DataFrame):
        raise EventSchemaError("events must be a pandas DataFrame")
    required = [*REQUIRED_COLUMNS, *(["matchId"] if require_match_id else [])]
    missing = [column for column in required if column not in events.columns]
    if missing:
        raise EventSchemaError(f"missing required event columns: {', '.join(missing)}")
    if events.empty:
        return events
    for column in ("eventId", "typeId", "periodId", "timeMin", "timeSec"):
        numeric = pd.to_numeric(events[column], errors="coerce")
        if numeric.isna().any():
            raise EventSchemaError(f"column {column!r} contains non-numeric or missing values")
    for column in ("x", "y"):
        numeric = pd.to_numeric(events[column], errors="coerce")
        # Opta records some out-of-play events just beyond the nominal pitch
        # boundary (the bundled real export reaches roughly -2..102).
        invalid = numeric.notna() & ~numeric.between(-5, 105)
        if invalid.any():
            raise EventSchemaError(f"column {column!r} contains implausible coordinates outside -5..105")
    if events["contestantId"].isna().any():
        raise EventSchemaError("column 'contestantId' contains missing values")
    return events
