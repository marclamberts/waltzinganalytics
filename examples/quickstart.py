"""Minimal end-to-end example: load a match and print set-piece metrics.

Run from the repo root:

    python examples/quickstart.py
"""

from pathlib import Path

from opta_setpieces import (
    delivery_locations,
    load_events,
    set_piece_goal_summary,
    set_piece_summary,
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
    print(delivery_locations(match.events, "corner").to_string(index=False))


if __name__ == "__main__":
    main()
