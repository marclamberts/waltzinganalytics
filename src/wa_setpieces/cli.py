"""Command-line entry point: ``wa-setpieces <match.json>``."""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from .core.loader import load_events
from .core.metrics import set_piece_summary
from .core.phases import second_phase_summary
from .core.retention import retention_rate
from .core.xt import XTModel, set_piece_xt_summary

_RETENTION_TYPES = ("kick_off", "free_kick", "corner", "throw_in", "goal_kick")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wa-setpieces",
        description="Summarize set-piece metrics from an Opta F24 JSON export.",
    )
    parser.add_argument("match_file", help="Path to an Opta F24 match JSON file")
    parser.add_argument(
        "--csv", metavar="PATH", help="Write the summary table to a CSV file instead of stdout"
    )
    parser.add_argument(
        "--xt",
        action="store_true",
        help=(
            "Also fit an xT grid on this match's events and print xT added for "
            "corner/free-kick deliveries. A single match is a very small sample "
            "for fitting xT -- treat the numbers as illustrative, not production."
        ),
    )
    args = parser.parse_args(argv)

    match = load_events(args.match_file)
    events = match.events

    summary = set_piece_summary(events)
    corner_phases = second_phase_summary(events, "corner")
    free_kick_phases = second_phase_summary(events, "free_kick")
    retention = pd.concat(
        [
            retention_rate(events, t).assign(set_piece_type=t)
            for t in _RETENTION_TYPES
            if not retention_rate(events, t).empty
        ],
        ignore_index=True,
    )

    with pd.option_context("display.max_rows", None, "display.width", 120):
        if args.csv:
            summary.to_csv(args.csv, index=False)
            print(f"Wrote {len(summary)} rows to {args.csv}")
        else:
            print("== Set-piece summary ==")
            print(summary.to_string(index=False))
            print()
            print("== Corner second phases ==")
            print(corner_phases.to_string(index=False) if not corner_phases.empty else "(none)")
            print()
            print("== Free-kick second phases ==")
            print(
                free_kick_phases.to_string(index=False) if not free_kick_phases.empty else "(none)"
            )
            print()
            print("== Retention (still in possession ~8s later) ==")
            print(retention.to_string(index=False) if not retention.empty else "(none)")

            if args.xt:
                print()
                print("== xT added (fit on this match only -- illustrative) ==")
                model = XTModel.fit(events)
                for sp_type in ("corner", "free_kick"):
                    print(f"-- {sp_type} --")
                    print(set_piece_xt_summary(events, sp_type, model).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
