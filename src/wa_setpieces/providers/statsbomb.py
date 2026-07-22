"""Convert a StatsBomb open-data match events export into the internal
events DataFrame every other ``wa_setpieces`` module consumes -- the same
shape :func:`wa_setpieces.core.loader.load_events`'s ``.events`` produces
from Opta F24. Once converted, ``wa_setpieces.core``, ``wa_setpieces.ml``,
``wa_setpieces.viz`` and ``wa_setpieces.core.rating`` all work unchanged on
StatsBomb data -- there is no separate StatsBomb code path anywhere else in
the package.

Coordinates are rescaled from StatsBomb's 120x80 pitch to Opta's 0-100 both
axes (both already the acting team's own attacking direction, so no flip is
needed). *Every* StatsBomb event is converted, not just passes and shots --
:mod:`wa_setpieces.core.retention` looks at "whichever team touched the
ball last in this window" across the *whole* event stream, so dropping
Carry/Pressure/Duel/etc. events would silently break it. Event types are
mapped onto the closest Opta ``typeId`` where a real equivalent exists
(Pass, Shot by outcome, Clearance, Foul Committed, Bad Behaviour/card,
Offside, Interception); anything else gets :data:`TYPE_OTHER` (0, unused by
Opta) -- it still counts as "a touch by this team" for retention, but
won't match any set-piece/shot/clearance/stoppage check.

**Known gap**: StatsBomb has no event type equivalent to Opta's distinct
"ball went out of play" event (``typeId`` 5, encoded on a pass's own
outcome instead) -- :mod:`wa_setpieces.core.phases`' second-phase window
stops early on that Opta event, so on StatsBomb data it can occasionally
run a few seconds longer in that specific case before its own time-window
cutoff takes over. Set-piece detection, the assist-chain shot link
(``key_pass_id``), retention, xT, added value and
:mod:`wa_setpieces.core.rating` do not depend on that event and are
unaffected.

No extra dependency is needed (unlike the ``viz``/``ml``/``convert``
extras) -- StatsBomb open-data ships as plain JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..core import constants as c

PITCH_LENGTH_M = 120.0
PITCH_WIDTH_M = 80.0

TYPE_OTHER = 0  # StatsBomb event types with no Opta typeId equivalent

_SHOT_OUTCOME_TYPE_ID = {
    "Goal": c.TYPE_GOAL,
    "Post": c.TYPE_POST,
    "Off T": c.TYPE_MISS,
    "Wayward": c.TYPE_MISS,
    "Blocked": c.TYPE_ATTEMPT_SAVED,
    "Saved": c.TYPE_ATTEMPT_SAVED,
    "Saved Off Target": c.TYPE_ATTEMPT_SAVED,
    "Saved to Post": c.TYPE_ATTEMPT_SAVED,
}

_PASS_SET_PIECE_QUALIFIER = {
    "Corner": c.QUALIFIER_CORNER_TAKEN,
    "Free Kick": c.QUALIFIER_FREE_KICK_TAKEN,
    "Throw-in": c.QUALIFIER_THROW_IN,
    "Goal Kick": c.QUALIFIER_GOAL_KICK,
    "Kick Off": c.QUALIFIER_KICK_OFF,
}

_SIMPLE_TYPE_ID = {
    "Clearance": c.TYPE_CLEARANCE,
    "Foul Committed": c.TYPE_FOUL,
    "Bad Behaviour": c.TYPE_CARD,
    "Offside": c.TYPE_OFFSIDE_PASS,
    "Interception": c.TYPE_INTERCEPTION,
}


def _to_opta_x(x: float | None) -> float | None:
    return round(x * 100.0 / PITCH_LENGTH_M, 2) if x is not None else None


def _to_opta_y(y: float | None) -> float | None:
    return round(y * 100.0 / PITCH_WIDTH_M, 2) if y is not None else None


def _load_raw(source: str | Path | list[dict]) -> list[dict]:
    if isinstance(source, (str, Path)):
        with Path(source).open(encoding="utf-8") as fh:
            return json.load(fh)
    return list(source)


def _convert_pass(ev: dict, qualifiers: dict[str, Any]) -> tuple[int, int]:
    pass_info = ev.get("pass", {}) or {}
    sp_qualifier = _PASS_SET_PIECE_QUALIFIER.get((pass_info.get("type") or {}).get("name"))
    if sp_qualifier is not None:
        qualifiers[f"q_{sp_qualifier}"] = True

    end_loc = pass_info.get("end_location") or []
    if len(end_loc) > 0 and end_loc[0] is not None:
        qualifiers[f"q_{c.QUALIFIER_PASS_END_X}"] = str(_to_opta_x(end_loc[0]))
    if len(end_loc) > 1 and end_loc[1] is not None:
        qualifiers[f"q_{c.QUALIFIER_PASS_END_Y}"] = str(_to_opta_y(end_loc[1]))

    technique = (pass_info.get("technique") or {}).get("name")
    if technique == "Inswinging":
        qualifiers["q_72"] = True
    elif technique == "Outswinging":
        qualifiers["q_224"] = True
    if (pass_info.get("body_part") or {}).get("name") == "Head":
        qualifiers[f"q_{c.QUALIFIER_HEAD_PASS}"] = True

    outcome = 0 if pass_info.get("outcome") is not None else 1
    return c.TYPE_PASS, outcome


def _convert_shot(ev: dict, qualifiers: dict[str, Any], id_to_index: dict[str, int]) -> tuple[int, int]:
    shot_info = ev.get("shot", {}) or {}
    outcome_name = (shot_info.get("outcome") or {}).get("name")
    type_id = _SHOT_OUTCOME_TYPE_ID.get(outcome_name, c.TYPE_MISS)

    if outcome_name == "Blocked":
        qualifiers["q_82"] = True
    if (shot_info.get("body_part") or {}).get("name") == "Head":
        qualifiers["q_22"] = True
    if (shot_info.get("type") or {}).get("name") == "Penalty":
        qualifiers[f"q_{c.QUALIFIER_PENALTY}"] = True

    xg = shot_info.get("statsbomb_xg")
    if xg is not None:
        qualifiers["q_103"] = str(round(xg * 100, 2))

    key_pass_id = shot_info.get("key_pass_id")
    if key_pass_id is not None and key_pass_id in id_to_index:
        qualifiers[f"q_{c.QUALIFIER_RELATED_EVENT_ID}"] = str(id_to_index[key_pass_id])

    return type_id, 1


def _convert_event(ev: dict, id_to_index: dict[str, int]) -> dict:
    type_name = (ev.get("type") or {}).get("name")
    qualifiers: dict[str, Any] = {}
    outcome = 1

    if type_name == "Pass":
        type_id, outcome = _convert_pass(ev, qualifiers)
    elif type_name == "Shot":
        type_id, outcome = _convert_shot(ev, qualifiers, id_to_index)
    else:
        type_id = _SIMPLE_TYPE_ID.get(type_name, TYPE_OTHER)

    team = ev.get("team") or {}
    player = ev.get("player") or {}
    location = ev.get("location") or []

    row = {
        "id": ev.get("id"),
        "eventId": ev.get("index"),
        "typeId": type_id,
        "periodId": ev.get("period"),
        "timeMin": ev.get("minute"),
        "timeSec": ev.get("second"),
        "contestantId": team.get("id"),
        "playerId": player.get("id"),
        "playerName": player.get("name"),
        "outcome": outcome,
        "x": _to_opta_x(location[0]) if len(location) > 0 else None,
        "y": _to_opta_y(location[1]) if len(location) > 1 else None,
        "timeStamp": ev.get("timestamp"),
    }
    row.update(qualifiers)
    return row


def load_statsbomb_events(source: str | Path | list[dict]) -> pd.DataFrame:
    """Parse a StatsBomb open-data events export (path to the match's
    ``events/<id>.json``, or an already-loaded list of event dicts) into
    the internal events DataFrame the rest of ``wa_setpieces`` consumes.

    Returns the same shape as :func:`wa_setpieces.core.loader.load_events`'s
    ``.events``: core columns (``id``, ``eventId``, ``typeId``, ...) plus
    ``q_<qualifierId>`` columns for whichever Opta qualifiers this module
    can derive from StatsBomb's differently-shaped event fields. See the
    module docstring for exactly what is (and isn't) faithfully mapped.
    """
    raw_events = _load_raw(source)
    id_to_index = {ev["id"]: ev.get("index") for ev in raw_events if "id" in ev}

    rows = [_convert_event(ev, id_to_index) for ev in raw_events]
    events = pd.DataFrame(rows)
    if not events.empty:
        events = events.sort_values(
            ["periodId", "timeMin", "timeSec", "eventId"]
        ).reset_index(drop=True)
    return events
