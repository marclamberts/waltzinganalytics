"""Run the complete wa-setpieces workflow on an Opta JSON file.

Examples
--------
Analyse corners and write results to ``analysis/``::

    python examples/analyse_opta.py match.json

Use a previously trained xT model::

    python examples/analyse_opta.py match.json --model league_xt.npz

Fit an illustrative model on this match (not recommended for production)::

    python examples/analyse_opta.py match.json --fit-match-xt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from wa_setpieces import (
    XTModel,
    defensive_rating,
    load_matches,
    run_workflow,
    validate_events,
    write_html_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse an Opta event file.")
    parser.add_argument("opta_file", type=Path, help="Path to the Opta JSON export")
    parser.add_argument(
        "--type",
        default="corner",
        choices=("corner", "free_kick", "throw_in", "goal_kick", "kick_off", "penalty"),
        help="Set-piece type to analyse (default: corner)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("analysis"), help="Output directory"
    )
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--model", type=Path, help="Previously saved XTModel .npz file")
    model_group.add_argument(
        "--fit-match-xt",
        action="store_true",
        help="Fit xT on this match; illustrative only because the sample is too small",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = validate_events(load_matches(args.opta_file))

    model = None
    if args.model:
        model = XTModel.load(args.model)
    elif args.fit_match_xt:
        model = XTModel.fit(events)

    result = run_workflow(events, args.type, model=model)
    args.output.mkdir(parents=True, exist_ok=True)

    tables = {
        name: value
        for name, value in vars(result).items()
        if isinstance(value, pd.DataFrame)
    }
    if not result.defensive_summary.empty:
        tables["defensive_rating"] = defensive_rating(result.defensive_summary)

    for name, table in tables.items():
        table.to_csv(args.output / f"{name}.csv", index=False)

    report_path = write_html_report(
        args.output / "report.html",
        title=f"{args.type.replace('_', ' ').title()} analysis",
        tables=tables,
        methodology=(
            "Source: Opta event data. Retention, phases, first contact and added value "
            "are derived event-data heuristics. Ratings need a season-sized benchmark."
        ),
    )

    print(result.summary.to_string(index=False))
    print(f"\nWrote {len(tables)} CSV files and {report_path}")
    if model is None and args.type in {"corner", "free_kick"}:
        print("Pass --model league_xt.npz to include added-value and player-rating outputs.")


if __name__ == "__main__":
    main()
