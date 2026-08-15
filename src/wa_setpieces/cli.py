"""Command-line tools for summaries, workflows, models and reports."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import pandas as pd
from .core.loader import load_events
from .core.metrics import set_piece_summary
from .core.workflow import run_workflow
from .core.xt import XTModel
from .providers.statsbomb import load_statsbomb_events
from .reporting import write_html_report

def _events(path: str, provider: str) -> pd.DataFrame:
    return load_events(path).events if provider == "opta" else load_statsbomb_events(path)

def _write(frame: pd.DataFrame, path: str | None, fmt: str) -> None:
    if path is None:
        print(frame.to_string(index=False))
    elif fmt == "csv": frame.to_csv(path, index=False)
    elif fmt == "parquet": frame.to_parquet(path, index=False)
    else: Path(path).write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wa-setpieces", description="Analyse football set pieces.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("summary", "workflow", "report"):
        cmd = sub.add_parser(name); cmd.add_argument("input")
        cmd.add_argument("--provider", choices=("opta", "statsbomb"), default="opta")
        if name != "summary": cmd.add_argument("--type", choices=("corner", "free_kick", "throw_in", "goal_kick", "kick_off", "penalty"), default="corner")
        if name == "summary":
            cmd.add_argument("--output"); cmd.add_argument("--format", choices=("csv", "json", "parquet"), default="csv")
        elif name == "workflow":
            cmd.add_argument("--model"); cmd.add_argument("--output", required=True, help="Directory for CSV workflow tables")
        else:
            cmd.add_argument("--model"); cmd.add_argument("--output", required=True, help="HTML output path")
    train = sub.add_parser("train-xt"); train.add_argument("inputs", nargs="+")
    train.add_argument("--provider", choices=("opta", "statsbomb"), default="opta")
    train.add_argument("--output", required=True); train.add_argument("--x-bins", type=int, default=16); train.add_argument("--y-bins", type=int, default=12)
    return parser

def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] not in {"summary", "workflow", "report", "train-xt", "-h", "--help"}:
        legacy = argparse.ArgumentParser(prog="wa-setpieces"); legacy.add_argument("input"); legacy.add_argument("--csv"); legacy.add_argument("--xt", action="store_true")
        old = legacy.parse_args(args_list); events = _events(old.input, "opta")
        _write(set_piece_summary(events), old.csv, "csv")
        if old.xt: print(pd.DataFrame(XTModel.fit(events).grid).to_string(index=False, header=False))
        return 0
    args = _parser().parse_args(args_list)
    if args.command == "train-xt":
        frames = [_events(path, args.provider).assign(matchId=Path(path).stem) for path in args.inputs]
        model = XTModel.fit(pd.concat(frames, ignore_index=True), x_bins=args.x_bins, y_bins=args.y_bins)
        model.metadata["sources"] = [str(path) for path in args.inputs]; model.save(args.output)
        print(json.dumps(model.metadata, indent=2)); return 0
    events = _events(args.input, args.provider)
    if args.command == "summary": _write(set_piece_summary(events), args.output, args.format); return 0
    model = XTModel.load(args.model) if args.model else None; result = run_workflow(events, args.type, model=model)
    tables = {name: value for name, value in vars(result).items() if isinstance(value, pd.DataFrame)}
    if args.command == "workflow":
        output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
        for name, table in tables.items(): table.to_csv(output / f"{name}.csv", index=False)
    else:
        write_html_report(args.output, f"{args.type.replace('_', ' ').title()} report", tables, methodology="Derived event-data heuristics; interpret small samples cautiously.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
