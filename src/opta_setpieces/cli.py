"""Command-line entry point: ``opta-setpieces <match.json>``."""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from .loader import load_events
from .metrics import set_piece_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="opta-setpieces",
        description="Summarize set-piece metrics from an Opta F24 JSON export.",
    )
    parser.add_argument("match_file", help="Path to an Opta F24 match JSON file")
    parser.add_argument(
        "--csv", metavar="PATH", help="Write the summary table to a CSV file instead of stdout"
    )
    args = parser.parse_args(argv)

    match = load_events(args.match_file)
    summary = set_piece_summary(match.events)

    with pd.option_context("display.max_rows", None, "display.width", 120):
        if args.csv:
            summary.to_csv(args.csv, index=False)
            print(f"Wrote {len(summary)} rows to {args.csv}")
        else:
            print(summary.to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
