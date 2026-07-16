"""Minimal end-to-end example: load a match and print set-piece metrics.

Run from the repo root:

    python examples/quickstart.py
"""

from pathlib import Path

from wa_setpieces import (
    XTModel,
    add_channels,
    delivery_locations,
    load_events,
    retention_rate,
    second_phase_summary,
    set_piece_goal_summary,
    set_piece_summary,
    set_piece_xt_summary,
)

DATA = Path(__file__).parent.parent / "tests" / "data" / "sample_match.json"


def main() -> None:
    match = load_events(DATA)
    print(f"Match status: {match.match_details['matchStatus']}")
    print(f"Final score: {match.match_details['scores']['total']}")
    print()

    print("== Set-piece summary (per team) ==")
    print(set_piece_summary(match.events).to_string(index=False))
    print()

    print("== Goals traced back to a set piece ==")
    goals = set_piece_goal_summary(match.events)
    print(goals.to_string(index=False) if not goals.empty else "(none this match)")
    print()

    print("== Corner delivery end locations ==")
    corners = delivery_locations(match.events, "corner")
    print(corners.to_string(index=False))
    print()

    print("== Corner delivery end channel (wide / half-space / central) ==")
    print(add_channels(corners, y_col="end_y", n=5)["channel"].value_counts())
    print()

    print("== Corner second phases (per team) ==")
    print(second_phase_summary(match.events, "corner").to_string(index=False))
    print()

    print("== Free-kick retention: still in possession ~8s later ==")
    print(retention_rate(match.events, "free_kick").to_string(index=False))
    print()

    print("== xT added by corner/free-kick deliveries ==")
    print("(fit on this single match -- illustrative only, see docs)")
    model = XTModel.fit(match.events)
    print(set_piece_xt_summary(match.events, "corner", model).to_string(index=False))
    print(set_piece_xt_summary(match.events, "free_kick", model).to_string(index=False))


if __name__ == "__main__":
    main()
