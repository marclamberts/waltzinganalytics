"""Possession retention after a set piece.

Opta's ``outcome`` flag on the restart pass itself only tells you whether
that one pass found a teammate. "Retention" here is broader and answers a
different question: did the team that took the set piece still have the
ball ``window_seconds`` later, or did the opponent win it back?

This is a derived heuristic (see :mod:`wa_setpieces.phases` for the same
caveat): it looks at which team's event is chronologically last inside the
time window following the restart.
"""

from __future__ import annotations

import pandas as pd

from .filters import tag_set_pieces

DEFAULT_WINDOW_SECONDS = 8.0


def _seconds(row: pd.Series) -> float:
    return float(row["timeMin"]) * 60.0 + float(row["timeSec"])


def _retained(events: pd.DataFrame, delivery_row: pd.Series, window_seconds: float) -> bool | None:
    period = delivery_row["periodId"]
    t0 = _seconds(delivery_row)
    pos = events.index.get_loc(delivery_row.name)
    later = events.iloc[pos + 1 :]
    later = later[later["periodId"] == period]
    if later.empty:
        return None
    times = later["timeMin"].astype(float) * 60.0 + later["timeSec"].astype(float)
    in_window = later[(times - t0) > 0][(times[(times - t0) > 0] - t0) <= window_seconds]
    if in_window.empty:
        # Nothing happened before the window closed (or before the period
        # ended) -- treat as retained, since no regain was observed.
        return True
    last_touch_team = in_window.iloc[-1]["contestantId"]
    return last_touch_team == delivery_row["contestantId"]


def retention_detail(
    events: pd.DataFrame,
    set_piece_type: str,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
) -> pd.DataFrame:
    """Per-delivery retention flag for one set-piece type.

    Args:
        set_piece_type: one of ``"kick_off"``, ``"free_kick"``, ``"corner"``,
            ``"throw_in"``, ``"goal_kick"`` (penalties are a shot, not a
            restart with a meaningful "retained possession after" concept,
            and are excluded).
        window_seconds: how long after the restart to check who has the ball.

    Returns:
        One row per delivery: eventId, contestantId, playerId, playerName,
        outcome (raw pass success), retained (bool or None if the period
        ended before the window closed).
    """
    if set_piece_type == "penalty":
        raise ValueError("retention is not meaningful for penalties")
    tagged = tag_set_pieces(events)
    deliveries = tagged.loc[tagged["set_piece_type"] == set_piece_type]

    records = []
    for _, row in deliveries.iterrows():
        records.append(
            {
                "eventId": row["eventId"],
                "contestantId": row["contestantId"],
                "playerId": row["playerId"],
                "playerName": row["playerName"],
                "outcome": row["outcome"],
                "retained": _retained(tagged, row, window_seconds),
            }
        )
    return pd.DataFrame.from_records(
        records,
        columns=["eventId", "contestantId", "playerId", "playerName", "outcome", "retained"],
    )


def retention_rate(
    events: pd.DataFrame,
    set_piece_type: str,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
) -> pd.DataFrame:
    """Per-team retention rate for one set-piece type.

    Rows where ``retained`` is ``None`` (period ended inside the window) are
    excluded from the rate but counted in ``deliveries``.
    """
    per_delivery = retention_detail(events, set_piece_type, window_seconds=window_seconds)
    if per_delivery.empty:
        return pd.DataFrame(columns=["contestantId", "deliveries", "retained", "retention_rate"])
    decided = per_delivery[per_delivery["retained"].notna()]
    out = (
        per_delivery.groupby("contestantId")
        .size()
        .rename("deliveries")
        .reset_index()
    )
    retained_counts = (
        decided.groupby("contestantId")["retained"].sum().rename("retained").reset_index()
    )
    decided_counts = (
        decided.groupby("contestantId").size().rename("decided").reset_index()
    )
    out = out.merge(retained_counts, on="contestantId", how="left")
    out = out.merge(decided_counts, on="contestantId", how="left")
    out["retained"] = out["retained"].fillna(0).astype(int)
    out["decided"] = out["decided"].fillna(0).astype(int)
    out["retention_rate"] = (out["retained"] / out["decided"].replace(0, pd.NA)).astype(float).round(3)
    return out.drop(columns="decided")
