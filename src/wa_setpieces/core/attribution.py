"""Transparent player attribution around set-piece deliveries."""

from __future__ import annotations

import pandas as pd

from .filters import tag_set_pieces


def first_contact_detail(
    events: pd.DataFrame, set_piece_type: str, *, window_seconds: float = 5.0
) -> pd.DataFrame:
    """Attribute the first subsequent on-ball event after each delivery.

    This is an event-order heuristic, not tracking-derived contact detection.
    ``confidence`` is therefore ``"event_sequence"`` and lets consumers keep
    inferred attribution distinct from provider-native facts.

    Match-safe: when ``matchId`` is present each match is walked
    independently, so a delivery near the end of one match can't pick up
    its "first contact" from the start of the next match in the frame.
    """
    if "matchId" not in events.columns:
        return _first_contact_detail_single(events, set_piece_type, window_seconds=window_seconds)
    frames = []
    for match_id, frame in events.groupby("matchId", sort=False):
        detail = _first_contact_detail_single(
            frame.drop(columns="matchId"), set_piece_type, window_seconds=window_seconds
        )
        detail.insert(0, "matchId", match_id)
        frames.append(detail)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["matchId"])


def _first_contact_detail_single(
    events: pd.DataFrame, set_piece_type: str, *, window_seconds: float = 5.0
) -> pd.DataFrame:
    tagged = tag_set_pieces(events).reset_index(drop=True)
    absolute = tagged["timeMin"].astype(float) * 60 + tagged["timeSec"].astype(float)
    rows = []
    for idx in tagged.index[tagged["set_piece_type"] == set_piece_type]:
        delivery = tagged.loc[idx]
        elapsed = absolute - absolute.loc[idx]
        candidates = tagged.loc[
            (tagged.index > idx) & (tagged["periodId"] == delivery["periodId"])
            & elapsed.between(0, window_seconds, inclusive="right")
            & tagged["playerId"].notna()
        ]
        contact = candidates.iloc[0] if not candidates.empty else None
        rows.append({
            "eventId": delivery["eventId"], "contestantId": delivery["contestantId"],
            "takerId": delivery.get("playerId"), "takerName": delivery.get("playerName"),
            "first_contact_player_id": None if contact is None else contact.get("playerId"),
            "first_contact_player_name": None if contact is None else contact.get("playerName"),
            "first_contact_team_id": None if contact is None else contact.get("contestantId"),
            "first_contact_won": None if contact is None else contact.get("contestantId") == delivery["contestantId"],
            "seconds_to_contact": None if contact is None else float(absolute.loc[contact.name] - absolute.loc[idx]),
            "confidence": "event_sequence",
        })
    return pd.DataFrame(rows)


def first_contact_summary(events: pd.DataFrame, set_piece_type: str, **kwargs) -> pd.DataFrame:
    detail = first_contact_detail(events, set_piece_type, **kwargs)
    if detail.empty:
        return pd.DataFrame(columns=["playerId", "playerName", "contacts", "contacts_won", "win_rate"])
    known = detail.loc[detail["first_contact_player_id"].notna()].copy()
    out = known.groupby(
        ["first_contact_player_id", "first_contact_player_name", "first_contact_team_id"], as_index=False
    ).agg(contacts=("eventId", "count"), contacts_won=("first_contact_won", "sum"))
    out["win_rate"] = (out["contacts_won"] / out["contacts"]).round(3)
    return out.rename(columns={"first_contact_player_id": "playerId", "first_contact_player_name": "playerName", "first_contact_team_id": "contestantId"})
