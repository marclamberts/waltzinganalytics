"""Convert an IMPECT event-data export (CSV) into the internal events
DataFrame every other ``wa_setpieces`` module consumes -- the same shape
:func:`wa_setpieces.core.loader.load_events`'s ``.events`` produces from
Opta. Once converted, ``wa_setpieces.core``, ``wa_setpieces.ml``,
``wa_setpieces.viz`` and ``wa_setpieces.core.rating`` all work unchanged on
IMPECT data -- there is no separate IMPECT code path anywhere else in the
package.

Verified against a real IMPECT export (one CSV covering 20 matches, ~53k
events, iteration 2128) -- see each mapping decision's comment below for
what was actually checked in that file, not assumed from a schema.

**Coordinates**: IMPECT's ``start.adjCoordinates.x``/``y`` (and ``end.``
equivalents) are already attacking-direction-normalized -- confirmed by
checking a team's own corners across both periods: the *raw*
``start.coordinates.x`` flips sign at half-time (a team's corners sit at
``x=52.5`` in period 1, ``x=-52.5`` in period 2, since the raw coordinate
is absolute pitch position), while ``adjCoordinates.x`` stays ``52.5`` in
both periods. Rescaled from IMPECT's centered 105x68m frame
(``x`` -52.5..52.5, ``y`` -34..34) to Opta's 0-100 both axes.

**One CSV, many matches**: unlike Opta/StatsBomb (one file per match),
an IMPECT export's own ``match_id`` column already covers many matches in
one file -- this module returns a ``matchId`` column already populated
from it, rather than requiring a filename-derived one the way
:func:`wa_setpieces.core.loader.load_events_multi` does for single-match
sources.

**Shot outcome**: ``result`` on a ``SHOT`` row is only ``SUCCESS``/``FAIL``
-- no saved/post/wide distinction the way Opta's ``typeId`` gives directly.
Mapped to :data:`~wa_setpieces.core.constants.TYPE_GOAL` /
:data:`~wa_setpieces.core.constants.TYPE_MISS` accordingly; this loses the
post/saved/wide split :func:`wa_setpieces.core.chains.link_set_piece_shots`
doesn't need (it only checks :data:`~wa_setpieces.core.constants.SHOT_TYPE_IDS`
membership) but a shot map colored by exact outcome would.

**GOAL rows are redundant, not additional**: every ``SHOT`` row with
``result == "SUCCESS"`` has a matching separate ``actionType == "GOAL"``
row (confirmed 1:1 in the reference export: 73 of each) -- logging the
same goal twice. The ``SHOT`` row already becomes
:data:`~wa_setpieces.core.constants.TYPE_GOAL` above, so the ``GOAL`` row
is mapped to :data:`TYPE_OTHER` here rather than double-counting it as a
second shot.

**Assist-chain linking**: IMPECT's ``setPiece.id`` groups a delivery with
everything that follows in the same phase (second balls, the eventual
shot), and ``setPiece.mainEvent`` flags which row in that group *is* the
delivery -- confirmed against a real corner-to-shot sequence in the
reference export. This module writes
:data:`~wa_setpieces.core.constants.QUALIFIER_RELATED_EVENT_ID` on a shot
using exactly that grouping, the IMPECT equivalent of Opta's own
assist-chain qualifier that :func:`wa_setpieces.core.chains.link_set_piece_shots`
reads.

**Known gap**: the export carries no player name field (only
``player.id``) -- ``playerName`` is ``None`` throughout. Anything that
labels output by player name (most ``label_col="playerName"`` plotting
defaults) needs an external id-to-name lookup merged in separately; this
module does not attempt to reconstruct one.

**Known gap**: no delivery-technique field (inswinger/outswinger) the way
StatsBomb's ``pass.technique`` gives directly -- :data:`~wa_setpieces.core.constants.QUALIFIER_INSWINGER`/
:data:`~wa_setpieces.core.constants.QUALIFIER_OUTSWINGER` are never set from
IMPECT data.

**Known gap**: period timing uses a documented but unverified-beyond-two-
periods assumption -- ``gameTime.gameTimeInSec`` restarts at a
``(periodId - 1) * 10000`` offset per period (confirmed for periods 1-2 in
the reference export: period 1 spans 0-2948s, period 2 spans
10000-13205s), and cumulative ``timeMin``/``timeSec`` here assumes 45-minute
halves the same way Opta's own clock does. Extra-time periods (3/4), if
present in a different export, would need checking against this same
assumption before trusting their derived ``timeMin``.

No extra dependency is needed (unlike the ``viz``/``ml``/``convert``
extras) -- IMPECT exports as plain CSV, just ``pandas``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..core import constants as c

PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
PERIOD_TIME_OFFSET_SEC = 10000.0
HALF_LENGTH_MIN = 45

TYPE_OTHER = 0  # IMPECT actionTypes with no Opta typeId equivalent

_CORE_FIELDS = (
    "matchId", "id", "eventId", "typeId", "periodId", "timeMin", "timeSec",
    "contestantId", "playerId", "playerName", "outcome", "x", "y", "timeStamp",
)

_SET_PIECE_QUALIFIER = {
    "CORNER": c.QUALIFIER_CORNER_TAKEN,
    "FREE_KICK": c.QUALIFIER_FREE_KICK_TAKEN,
    "THROW_IN": c.QUALIFIER_THROW_IN,
    "GOAL_KICK": c.QUALIFIER_GOAL_KICK,
    "KICK_OFF": c.QUALIFIER_KICK_OFF,
}

_SIMPLE_TYPE_ID = {
    "CLEARANCE": c.TYPE_CLEARANCE,
    "INTERCEPTION": c.TYPE_INTERCEPTION,
    "FOUL": c.TYPE_FOUL,
    "YELLOW_CARD": c.TYPE_CARD,
    "SECOND_YELLOW_CARD": c.TYPE_CARD,
    "RED_CARD": c.TYPE_CARD,
    "OFFSIDE": c.TYPE_OFFSIDE_PASS,
    "OUT": c.TYPE_OUT,
    "GK_SAVE": c.TYPE_SAVE,
    "GK_CATCH": c.TYPE_CLAIM,
    "GROUND_DUEL": c.TYPE_TACKLE,
}


def _to_opta_x(x: Any) -> float | None:
    if x is None or pd.isna(x):
        return None
    return round((float(x) + PITCH_LENGTH_M / 2) / PITCH_LENGTH_M * 100.0, 2)


def _to_opta_y(y: Any) -> float | None:
    if y is None or pd.isna(y):
        return None
    return round((float(y) + PITCH_WIDTH_M / 2) / PITCH_WIDTH_M * 100.0, 2)


def _clean_id(value: Any) -> str | None:
    """``426.0`` (pandas' float read of an integer CSV column) -> ``"426"``."""
    if value is None or pd.isna(value):
        return None
    return str(int(value))


def _cumulative_time(game_time_sec: Any, period_id: Any) -> tuple[int | None, int | None]:
    if game_time_sec is None or pd.isna(game_time_sec) or period_id is None or pd.isna(period_id):
        return None, None
    elapsed = float(game_time_sec) - (float(period_id) - 1) * PERIOD_TIME_OFFSET_SEC
    cumulative = elapsed + (float(period_id) - 1) * HALF_LENGTH_MIN * 60
    cumulative = max(cumulative, 0.0)
    return int(cumulative // 60), int(cumulative % 60)


def _load_raw(source: str | Path | pd.DataFrame) -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        return source.copy()
    return pd.read_csv(source)


def _pass_qualifiers(row: pd.Series) -> dict[str, Any]:
    qualifiers: dict[str, Any] = {}
    end_x = _to_opta_x(row.get("end.adjCoordinates.x"))
    end_y = _to_opta_y(row.get("end.adjCoordinates.y"))
    if end_x is not None:
        qualifiers[f"q_{c.QUALIFIER_PASS_END_X}"] = str(end_x)
    if end_y is not None:
        qualifiers[f"q_{c.QUALIFIER_PASS_END_Y}"] = str(end_y)
    if row.get("bodyPart") == "HEAD":
        qualifiers[f"q_{c.QUALIFIER_HEAD_PASS}"] = True
    return qualifiers


def load_impect_events(source: str | Path | pd.DataFrame) -> pd.DataFrame:
    """Parse an IMPECT event export (CSV path, or an already-loaded
    DataFrame in the raw IMPECT column shape) into the internal events
    DataFrame the rest of ``wa_setpieces`` consumes.

    Returns the same shape as :func:`wa_setpieces.core.loader.load_events`'s
    ``.events``, plus a populated ``matchId`` column (IMPECT's own
    ``match_id``, since one export commonly covers many matches -- see the
    module docstring). See the module docstring for exactly what is (and
    isn't) faithfully mapped.
    """
    raw = _load_raw(source)
    if raw.empty:
        return pd.DataFrame(columns=list(_CORE_FIELDS))

    # A handful of actionTypes (NO_VIDEO, FINAL_WHISTLE, REFEREE_INTERCEPTION
    # -- confirmed exhaustive against the reference export) carry no
    # squadId at all: administrative markers, not a touch by either team,
    # so there's no meaningful (matchId, contestantId)-scoped eventId to
    # assign them. Dropped rather than kept with a null eventId, which
    # core.schema.validate_events (via SeasonDataset) rejects outright.
    raw = raw.dropna(subset=["squadId"])
    raw = raw.sort_values(["match_id", "index"], kind="stable").reset_index(drop=True)
    # Team-scoped, sequential per match -- the same numbering convention
    # Opta's own feed uses (both teams number their own events 1, 2, 3, ...
    # independently; see core.chains' module docstring for why every
    # eventId-based lookup in this package is scoped to (matchId,
    # contestantId) as a result).
    raw["_eventId"] = raw.groupby(["match_id", "squadId"]).cumcount() + 1
    id_to_event = {
        row["id"]: (row["match_id"], row["squadId"], row["_eventId"])
        for row in raw[["id", "match_id", "squadId", "_eventId"]].to_dict("records")
    }

    # setPiece.id/setPiece.mainEvent are optional enrichment columns -- a
    # stripped or older export may not carry them at all. Assist-chain
    # linking is then simply unavailable (q_55 never gets set), not an
    # error: everything else in this module still works.
    if "setPiece.mainEvent" in raw.columns and "setPiece.id" in raw.columns:
        main_events = raw.loc[raw["setPiece.mainEvent"] == True, ["setPiece.id", "id", "squadId"]]  # noqa: E712
        main_event_by_group = main_events.set_index("setPiece.id") if not main_events.empty else main_events
    else:
        main_event_by_group = pd.DataFrame(columns=["id", "squadId"])

    rows = []
    for row in raw.to_dict("records"):
        action_type = row.get("actionType")
        qualifiers: dict[str, Any] = {}

        if action_type == "GOAL":
            type_id = TYPE_OTHER
        elif action_type == "SHOT":
            type_id = c.TYPE_GOAL if row.get("result") == "SUCCESS" else c.TYPE_MISS
            if row.get("action") == "PENALTY_KICK":
                qualifiers[f"q_{c.QUALIFIER_PENALTY}"] = True
            if row.get("bodyPart") == "HEAD":
                qualifiers[f"q_{c.QUALIFIER_HEADED}"] = True
            sp_id = row.get("setPiece.id")
            if sp_id is not None and not pd.isna(sp_id) and not main_event_by_group.empty and sp_id in main_event_by_group.index:
                main = main_event_by_group.loc[sp_id]
                if isinstance(main, pd.DataFrame):  # duplicate mainEvent flags; defensive
                    main = main.iloc[0]
                if main["squadId"] == row.get("squadId") and main["id"] != row.get("id"):
                    _, _, main_event_id = id_to_event[main["id"]]
                    qualifiers[f"q_{c.QUALIFIER_RELATED_EVENT_ID}"] = str(main_event_id)
        elif row.get("duel.duelType") == "AERIAL_DUEL":
            type_id = c.TYPE_AERIAL
        elif action_type in _SET_PIECE_QUALIFIER:
            type_id = c.TYPE_PASS
            qualifiers[f"q_{_SET_PIECE_QUALIFIER[action_type]}"] = True
            qualifiers.update(_pass_qualifiers(row))
        elif action_type == "PASS":
            type_id = c.TYPE_PASS
            qualifiers.update(_pass_qualifiers(row))
        else:
            type_id = _SIMPLE_TYPE_ID.get(action_type, TYPE_OTHER)

        result = row.get("result")
        outcome = 0 if result in ("FAIL", "NEUTRAL") else 1

        time_min, time_sec = _cumulative_time(row.get("gameTime.gameTimeInSec"), row.get("periodId"))

        record = {
            "matchId": _clean_id(row.get("match_id")),
            "id": row.get("id"),
            "eventId": id_to_event[row["id"]][2],
            "typeId": type_id,
            "periodId": int(row["periodId"]) if row.get("periodId") is not None and not pd.isna(row.get("periodId")) else None,
            "timeMin": time_min,
            "timeSec": time_sec,
            "contestantId": _clean_id(row.get("squadId")),
            "playerId": _clean_id(row.get("player.id")),
            "playerName": None,
            "outcome": outcome,
            "x": _to_opta_x(row.get("start.adjCoordinates.x")),
            "y": _to_opta_y(row.get("start.adjCoordinates.y")),
            "timeStamp": None,
        }
        record.update(qualifiers)
        rows.append(record)

    events = pd.DataFrame(rows)
    events = events.sort_values(
        ["matchId", "periodId", "timeMin", "timeSec", "eventId"], na_position="last"
    ).reset_index(drop=True)
    return events
