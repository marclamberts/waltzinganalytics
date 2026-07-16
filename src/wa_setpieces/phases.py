"""Second-phase detection for corners and free kicks.

Opta's F24 feed has no explicit "phase" or "possession chain" field, so
this is a derived heuristic, not a raw data attribute -- treat it as an
estimate and tune the thresholds for your use case.

The heuristic walks the event stream forward from a corner/free-kick
delivery and classifies what happened to the ball:

- **Cleared immediately**: the defending team's first meaningful touch is a
  clearance/save/claim that sends the ball back up the pitch past
  ``clear_safe_x`` (using the confirmed F24 convention that every event's
  ``x`` is in *that event's own team's* attacking direction, i.e. low ``x``
  = deep in that team's own defensive zone -- see :mod:`wa_setpieces.zones`).
- **First-phase shot**: the attacking team shoots directly off the delivery
  (the very next event in the window is a shot).
- **Second-phase shot**: the ball stays alive near the defending team's goal
  (a loose ball, knockdown, or blocked/partial clearance) and the attacking
  team gets a further shot away before the danger is cleared or the ball
  goes dead.
- Anything else (ball goes out of play, a foul/offside interrupts play, or
  the window runs out with no shot) is recorded with no phase-2 shot.

A window is bounded by ``max_gap_seconds`` between consecutive events (a
bigger gap means open play has resumed), ``max_total_seconds`` since the
delivery, and ``max_events``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import constants as c
from .filters import extract_corners, extract_free_kicks

DEFAULT_CLEAR_SAFE_X = 45.0
DEFAULT_MAX_GAP_SECONDS = 8.0
DEFAULT_MAX_TOTAL_SECONDS = 20.0
DEFAULT_MAX_EVENTS = 25

_DEFENSIVE_CLEAR_TYPE_IDS = frozenset({c.TYPE_CLEARANCE, c.TYPE_SAVE, c.TYPE_CLAIM})
_STOPPAGE_TYPE_IDS = frozenset({c.TYPE_FOUL, c.TYPE_OFFSIDE_PASS, c.TYPE_CARD})


def _seconds(row: pd.Series) -> float:
    return float(row["timeMin"]) * 60.0 + float(row["timeSec"])


def _team_ids(events: pd.DataFrame) -> tuple[str, str]:
    teams = [t for t in events["contestantId"].dropna().unique()]
    if len(teams) != 2:
        raise ValueError(f"expected exactly 2 teams in events, found {len(teams)}")
    return teams[0], teams[1]


def _other_team(team: str, teams: tuple[str, str]) -> str:
    return teams[1] if team == teams[0] else teams[0]


def _phase_window(
    events: pd.DataFrame,
    start_pos: int,
    period_id: int,
    t0: float,
    max_gap_seconds: float,
    max_total_seconds: float,
    max_events: int,
) -> pd.DataFrame:
    rows = []
    prev_t = t0
    for pos in range(start_pos, min(start_pos + max_events, len(events))):
        row = events.iloc[pos]
        if row["periodId"] != period_id:
            break
        t = _seconds(row)
        if t - t0 > max_total_seconds:
            break
        if t - prev_t > max_gap_seconds:
            break
        rows.append(row)
        prev_t = t
    return pd.DataFrame(rows)


@dataclass
class PhaseResult:
    delivery_event_id: int
    set_piece_type: str
    contestant_id: str
    opponent_id: str
    first_contact_event_id: float | None
    first_contact_team: str | None
    first_contact_type_id: float | None
    cleared_immediately: bool
    second_phase_shot: bool
    second_phase_event_id: float | None
    second_phase_is_goal: bool
    phase_events_n: int

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def classify_phase(
    events: pd.DataFrame,
    delivery_row: pd.Series,
    clear_safe_x: float = DEFAULT_CLEAR_SAFE_X,
    max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
    max_total_seconds: float = DEFAULT_MAX_TOTAL_SECONDS,
    max_events: int = DEFAULT_MAX_EVENTS,
) -> PhaseResult:
    """Classify the phase(s) following a single corner/free-kick delivery."""
    teams = _team_ids(events)
    attacking_team = delivery_row["contestantId"]
    defending_team = _other_team(attacking_team, teams)

    pos = events.index.get_loc(delivery_row.name)
    window = _phase_window(
        events,
        pos + 1,
        delivery_row["periodId"],
        _seconds(delivery_row),
        max_gap_seconds,
        max_total_seconds,
        max_events,
    )

    result = PhaseResult(
        delivery_event_id=delivery_row["eventId"],
        set_piece_type=delivery_row["set_piece_type"]
        if "set_piece_type" in delivery_row
        else None,
        contestant_id=attacking_team,
        opponent_id=defending_team,
        first_contact_event_id=None,
        first_contact_team=None,
        first_contact_type_id=None,
        cleared_immediately=False,
        second_phase_shot=False,
        second_phase_event_id=None,
        second_phase_is_goal=False,
        phase_events_n=len(window),
    )

    if window.empty:
        return result

    first = window.iloc[0]
    result.first_contact_event_id = first["eventId"]
    result.first_contact_team = first["contestantId"]
    result.first_contact_type_id = first["typeId"]

    for i, (_, row) in enumerate(window.iterrows()):
        if row["typeId"] == c.TYPE_OUT:
            break

        if row["typeId"] in c.SHOT_TYPE_IDS and row["contestantId"] == attacking_team:
            if i == 0:
                # Direct shot off the delivery itself -- first-phase, not second.
                break
            result.second_phase_shot = True
            result.second_phase_event_id = row["eventId"]
            result.second_phase_is_goal = row["typeId"] == c.TYPE_GOAL
            break

        if (
            row["contestantId"] == defending_team
            and row["typeId"] in _DEFENSIVE_CLEAR_TYPE_IDS
            and float(row["x"]) > clear_safe_x
        ):
            result.cleared_immediately = i == 0
            break

        if row["typeId"] in _STOPPAGE_TYPE_IDS:
            break

    return result


_EXTRACTORS = {"corner": extract_corners, "free_kick": extract_free_kicks}


def second_phases(
    events: pd.DataFrame,
    set_piece_type: str,
    clear_safe_x: float = DEFAULT_CLEAR_SAFE_X,
    max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
    max_total_seconds: float = DEFAULT_MAX_TOTAL_SECONDS,
    max_events: int = DEFAULT_MAX_EVENTS,
) -> pd.DataFrame:
    """Classify second phases for every delivery of one set-piece type.

    Args:
        set_piece_type: ``"corner"`` or ``"free_kick"``.

    Returns:
        One row per delivery with columns matching :class:`PhaseResult`.
    """
    if set_piece_type not in _EXTRACTORS:
        raise ValueError(
            f"set_piece_type must be one of {sorted(_EXTRACTORS)}, got {set_piece_type!r}"
        )
    deliveries = _EXTRACTORS[set_piece_type](events)
    records = []
    for _, delivery_row in deliveries.iterrows():
        delivery_row = delivery_row.copy()
        delivery_row["set_piece_type"] = set_piece_type
        result = classify_phase(
            events,
            delivery_row,
            clear_safe_x=clear_safe_x,
            max_gap_seconds=max_gap_seconds,
            max_total_seconds=max_total_seconds,
            max_events=max_events,
        )
        records.append(result.as_dict())
    if not records:
        return pd.DataFrame(columns=list(PhaseResult.__annotations__))
    return pd.DataFrame.from_records(records)


def second_phase_summary(events: pd.DataFrame, set_piece_type: str) -> pd.DataFrame:
    """Per-team roll-up: deliveries, second phases created, and second-phase goals."""
    phases = second_phases(events, set_piece_type)
    if phases.empty:
        return pd.DataFrame(
            columns=["contestantId", "deliveries", "second_phases", "second_phase_goals"]
        )
    out = (
        phases.groupby("contestant_id")
        .agg(
            deliveries=("delivery_event_id", "count"),
            second_phases=("second_phase_shot", "sum"),
            second_phase_goals=("second_phase_is_goal", "sum"),
        )
        .reset_index()
        .rename(columns={"contestant_id": "contestantId"})
    )
    return out
