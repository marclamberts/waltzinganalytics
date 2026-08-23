"""Command-line tools for summaries, workflows, models and reports."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import pandas as pd
from .core.loader import load_matches
from .core.metrics import set_piece_summary
from .core.season import SeasonDataset
from .core.workflow import run_workflow
from .core.xt import XTModel
from .reporting import opponent_scouting_report_html, save_tables, write_html_report

_COMMANDS = {"summary", "workflow", "report", "season", "scout", "train-xt", "-h", "--help"}
_SET_PIECE_TYPES = ("corner", "free_kick", "throw_in", "goal_kick", "kick_off", "penalty")
_SEASON_ACTIONS = ("summary", "report", "season-report", "rolling", "rolling-defense")
_PROVIDERS = ("opta", "statsbomb", "impect")

def _events(path: str, provider: str) -> pd.DataFrame:
    # `input`/`inputs` below accept a single file or a whole folder --
    # load_matches itself now requires an explicit type=, so this is
    # where "which one did the user actually pass" gets resolved. For a
    # folder (or a multi-match IMPECT CSV, which covers many matches in
    # one file already) this returns every match's events combined, with
    # a matchId column, same as `season` below. Fine for the aggregate
    # commands (summary/workflow/report); phase-window-sensitive analysis
    # across a genuinely multi-match input should go through `season`
    # instead -- see load_matches' docstring for why.
    type_ = "season" if Path(path).is_dir() else "match"
    return load_matches(path, provider=provider, type=type_)

def _write(frame: pd.DataFrame, path: str | None, fmt: str) -> None:
    if path is None:
        print(frame.to_string(index=False))
    elif fmt == "csv": frame.to_csv(path, index=False)
    elif fmt == "parquet": frame.to_parquet(path, index=False)
    else: Path(path).write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")

def _season_from_inputs(inputs: list[str], provider: str) -> SeasonDataset:
    # Each entry in `inputs` can itself be a single file or a folder --
    # load_matches resolves either, per provider, and load_matches' own
    # duplicate-matchId check catches collisions *within* one input. This
    # checks *across* inputs -- e.g. two folders (or an IMPECT CSV passed
    # twice) contributing the same match. A matchId naturally repeats
    # across every one of its own event rows within a single frame, so
    # the check compares each input's *set* of matchIds, not raw rows.
    frames = [
        load_matches(path, provider=provider, type="season" if Path(path).is_dir() else "match")
        for path in inputs
    ]
    seen: dict[str, str] = {}
    for path, frame in zip(inputs, frames):
        for match_id in frame["matchId"].unique():
            if match_id in seen:
                raise ValueError(
                    f"duplicate matchId {match_id!r} from {seen[match_id]!r} and {path!r} "
                    "would silently merge distinct matches"
                )
            seen[match_id] = path
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return SeasonDataset(combined)

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wa-setpieces", description="Analyse football set pieces.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("summary", "workflow", "report"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", help="A single match file, or a folder of them (*.json/*.csv per --provider)")
        cmd.add_argument("--provider", choices=_PROVIDERS, default="opta")
        if name != "summary": cmd.add_argument("--type", choices=_SET_PIECE_TYPES, default="corner")
        if name == "summary":
            cmd.add_argument("--output"); cmd.add_argument("--format", choices=("csv", "json", "parquet"), default="csv")
        elif name == "workflow":
            cmd.add_argument("--model")
            cmd.add_argument("--output", required=True, help="Directory for workflow tables")
            cmd.add_argument("--format", choices=("csv", "xlsx"), default="csv")
        else:
            cmd.add_argument("--model"); cmd.add_argument("--output", required=True, help="HTML output path")

    scout = sub.add_parser("scout", help="Opponent scouting report: how a team defends a set piece")
    scout.add_argument("input", help="A single match file, or a folder of them (*.json/*.csv per --provider)")
    scout.add_argument("--provider", choices=_PROVIDERS, default="opta")
    scout.add_argument("--type", choices=_SET_PIECE_TYPES, default="corner")
    scout.add_argument("--opponent", required=True, help="contestantId to scout -- see `wa-setpieces summary` for IDs")
    scout.add_argument("--team-name", help="Display name for the opponent (defaults to their contestantId)")
    scout.add_argument("--output", required=True, help="HTML output path")

    season = sub.add_parser("season", help="Multi-match aggregation via SeasonDataset")
    season.add_argument(
        "inputs", nargs="+",
        help="One or more match files or folders (a folder loads every file in it -- "
             "*.json for opta/statsbomb, *.csv for impect). Opta/StatsBomb files are "
             "tagged with their filename as matchId; IMPECT uses the export's own match_id.",
    )
    season.add_argument("--provider", choices=_PROVIDERS, default="opta")
    season.add_argument("--action", choices=_SEASON_ACTIONS, default="summary")
    season.add_argument("--type", choices=_SET_PIECE_TYPES, default="corner", help="Needed for report/season-report")
    season.add_argument("--model", help="Needed for added value in report/season-report")
    season.add_argument("--window", type=int, default=5, help="Trailing-match window for rolling/rolling-defense")
    season.add_argument("--output"); season.add_argument("--format", choices=("csv", "json", "parquet"), default="csv")

    train = sub.add_parser("train-xt")
    train.add_argument("inputs", nargs="+", help="One or more match files or folders, as in `season`")
    train.add_argument("--provider", choices=_PROVIDERS, default="opta")
    train.add_argument("--output", required=True); train.add_argument("--x-bins", type=int, default=16); train.add_argument("--y-bins", type=int, default=12)
    return parser

def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] not in _COMMANDS:
        legacy = argparse.ArgumentParser(prog="wa-setpieces"); legacy.add_argument("input"); legacy.add_argument("--csv"); legacy.add_argument("--xt", action="store_true")
        old = legacy.parse_args(args_list); events = _events(old.input, "opta")
        _write(set_piece_summary(events), old.csv, "csv")
        if old.xt: print(pd.DataFrame(XTModel.fit(events).grid).to_string(index=False, header=False))
        return 0
    args = _parser().parse_args(args_list)

    if args.command == "train-xt":
        frames = [
            load_matches(path, provider=args.provider, type="season" if Path(path).is_dir() else "match")
            for path in args.inputs
        ]
        model = XTModel.fit(pd.concat(frames, ignore_index=True), x_bins=args.x_bins, y_bins=args.y_bins)
        model.metadata["sources"] = [str(path) for path in args.inputs]; model.save(args.output)
        print(json.dumps(model.metadata, indent=2)); return 0

    if args.command == "scout":
        events = _events(args.input, args.provider)
        html = opponent_scouting_report_html(events, args.opponent, args.type, team_name=args.team_name)
        Path(args.output).write_text(html, encoding="utf-8")
        return 0

    if args.command == "season":
        season = _season_from_inputs(args.inputs, args.provider)
        model = XTModel.load(args.model) if args.model else None
        if args.action == "summary": result = season.summary()
        elif args.action == "report": result = season.report(args.type, model=model)
        elif args.action == "season-report": result = season.season_report(args.type, model=model)
        elif args.action == "rolling": result = season.rolling_summary(window=args.window)
        else: result = season.rolling_defensive_summary(window=args.window)
        _write(result, args.output, args.format)
        return 0

    events = _events(args.input, args.provider)
    if args.command == "summary": _write(set_piece_summary(events), args.output, args.format); return 0

    model = XTModel.load(args.model) if args.model else None
    if args.command == "report" and args.type == "corner":
        # The curated corner report (rating, outcome/routine breakdowns, and
        # delivery/outcome maps if the viz extra is installed) rather than a
        # raw dump of run_workflow's tables -- see corner_report_html's
        # docstring. Other set-piece types fall through to the generic dump
        # below since there's no equivalent curated report for them yet.
        from .reporting import corner_report_html
        Path(args.output).write_text(corner_report_html(events, model=model), encoding="utf-8")
        return 0

    result = run_workflow(events, args.type, model=model)
    tables = {name: value for name, value in vars(result).items() if isinstance(value, pd.DataFrame)}
    if args.command == "workflow":
        save_tables(tables, args.output, fmt=args.format)
    else:
        write_html_report(args.output, f"{args.type.replace('_', ' ').title()} report", tables, methodology="Derived event-data heuristics; interpret small samples cautiously.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
