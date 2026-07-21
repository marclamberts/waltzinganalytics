"""Link set pieces to the shots and goals they produce.

Opta connects a shot to the pass that created it via qualifier 55
("related event id"), which stores the ``eventId`` of the assisting pass.
A shot can also *be* a set piece directly (e.g. a direct free kick or a
penalty), in which case there is no separate assisting pass to look up.

``eventId`` is only unique *within one team's own event stream* -- both
teams number their events 1, 2, 3, ... independently (confirmed against
``tests/data/sample_match.json``: 1464 of 1613 rows share an ``eventId``
with a same-numbered row from the other team; the globally unique field is
``id``). An assist is always played by a teammate, so qualifier 55's
``eventId`` is resolved scoped to the shot's own ``contestantId`` --
without that scoping, a lookup by ``eventId`` alone can silently resolve
to the *other* team's event of the same number.
"""

from __future__ import annotations

import pandas as pd

from . import constants as c
from .filters import tag_set_pieces


def link_set_piece_shots(events: pd.DataFrame) -> pd.DataFrame:
    """Return one row per shot (incl. goals) with its set-piece origin, if any.

    Columns:
        eventId, typeId, outcome, is_goal, contestantId, playerId, playerName,
        x, y, timeMin, timeSec, set_piece_type, set_piece_event_id.

    ``set_piece_type`` is ``None`` for shots that did not originate from a
    tagged set piece (open play, or a phase the assist qualifier does not
    reach back to).
    """
    tagged = tag_set_pieces(events)
    shots = tagged.loc[tagged["typeId"].isin(c.SHOT_TYPE_IDS)].copy()

    # Indexed by (contestantId, eventId), which is the actually-unique key --
    # see module docstring for why eventId alone is not safe to index on.
    by_team_event = tagged.set_index(["contestantId", "eventId"], drop=False)

    set_piece_type: list[str | None] = []
    set_piece_event_id: list[int | None] = []
    for _, shot in shots.iterrows():
        # Case 1: the shot itself is the set piece (direct free kick, penalty).
        if shot["set_piece_type"] is not None:
            set_piece_type.append(shot["set_piece_type"])
            set_piece_event_id.append(shot["eventId"])
            continue

        # Case 2: walk back to the assisting pass via qualifier 55, scoped to
        # the shooting team's own event stream (an assist is always a teammate).
        related_raw = shot.get(f"q_{c.QUALIFIER_RELATED_EVENT_ID}")
        origin_type = None
        origin_event_id = None
        if related_raw is not None:
            try:
                related_id = int(float(related_raw))
            except (TypeError, ValueError):
                related_id = None
            key = (shot["contestantId"], related_id)
            if related_id is not None and key in by_team_event.index:
                origin = by_team_event.loc[key]
                if isinstance(origin, pd.DataFrame):  # defensive; shouldn't occur
                    origin = origin.iloc[0]
                if origin["set_piece_type"] is not None:
                    origin_type = origin["set_piece_type"]
                    origin_event_id = int(related_id)
        set_piece_type.append(origin_type)
        set_piece_event_id.append(origin_event_id)

    shots["is_goal"] = shots["typeId"] == c.TYPE_GOAL
    shots["set_piece_type"] = set_piece_type
    shots["set_piece_event_id"] = set_piece_event_id

    cols = [
        "eventId",
        "typeId",
        "outcome",
        "is_goal",
        "contestantId",
        "playerId",
        "playerName",
        "x",
        "y",
        "timeMin",
        "timeSec",
        "set_piece_type",
        "set_piece_event_id",
    ]
    return shots[cols].reset_index(drop=True)


def set_piece_goal_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Goals scored per set-piece type per team.

    Returns a DataFrame indexed by ``(contestantId, set_piece_type)`` with a
    ``goals`` count, restricted to set pieces that produced at least one goal.
    """
    linked = link_set_piece_shots(events)
    goals = linked.loc[linked["is_goal"] & linked["set_piece_type"].notna()]
    if goals.empty:
        return pd.DataFrame(columns=["contestantId", "set_piece_type", "goals"])
    summary = (
        goals.groupby(["contestantId", "set_piece_type"])
        .size()
        .rename("goals")
        .reset_index()
    )
    return summary
