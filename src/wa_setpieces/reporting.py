"""Portable HTML reports with embedded tables and optional figures."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from html import escape

import pandas as pd


def _figure_data_uri(fig) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def render_html_report(
    title: str,
    tables: dict[str, pd.DataFrame],
    *,
    figures: dict[str, object] | None = None,
    methodology: str | None = None,
) -> str:
    """Render a self-contained analytical report as an HTML string."""
    sections = []
    for name, table in tables.items():
        sections.append(f"<section><h2>{escape(name)}</h2>{table.to_html(index=False, border=0, classes='data')}</section>")
    for name, fig in (figures or {}).items():
        sections.append(f'<section><h2>{escape(name)}</h2><img src="{_figure_data_uri(fig)}" alt="{escape(name)}"></section>')
    note = f"<aside><h2>Methodology</h2><p>{escape(methodology)}</p></aside>" if methodology else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{escape(title)}</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#172033}}h1{{border-bottom:3px solid #ef7d00;padding-bottom:12px}}section,aside{{margin:30px 0}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:7px;border-bottom:1px solid #d8dee9;text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{background:#edf2f7}}img{{max-width:100%;height:auto}}aside{{background:#f5f7fa;padding:16px}}</style></head><body><h1>{escape(title)}</h1>{''.join(sections)}{note}</body></html>"""


def write_html_report(path: str | Path, title: str, tables: dict[str, pd.DataFrame], **kwargs) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_html_report(title, tables, **kwargs), encoding="utf-8")
    return target


def save_table(table: pd.DataFrame, path: str | Path, **kwargs) -> Path:
    """Save any DataFrame this package produces to CSV or Excel, chosen by
    ``path``'s file extension -- ``delivery_outcomes``, ``corner_report``,
    ``cluster_routines``, anything.

    Args:
        table: any DataFrame.
        path: output path; ``.csv`` or ``.xlsx``/``.xls`` picks the format
            (anything else raises). Parent directories are created if
            they don't exist.
        **kwargs: forwarded to :meth:`pandas.DataFrame.to_csv` /
            :meth:`~pandas.DataFrame.to_excel`. ``index`` defaults to
            ``False`` (most tables here have no meaningful row index).

    Returns:
        ``path``, as a :class:`~pathlib.Path`.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower()
    kwargs.setdefault("index", False)
    if suffix == ".csv":
        table.to_csv(target, **kwargs)
    elif suffix in (".xlsx", ".xls"):
        try:
            table.to_excel(target, **kwargs)
        except ImportError as exc:
            raise ImportError(
                'writing .xlsx/.xls needs the \'xlsx\' extra: pip install "wa-setpieces[xlsx]"'
            ) from exc
    else:
        raise ValueError(f"unsupported file extension {suffix!r} -- use .csv, .xlsx or .xls")
    return target


def save_tables(
    tables: dict[str, pd.DataFrame], directory: str | Path, fmt: str = "csv", **kwargs
) -> dict[str, Path]:
    """Save several named tables into one directory, one file per table --
    e.g. a :class:`~wa_setpieces.core.workflow.SetPieceWorkflow`'s tables.

    Args:
        tables: ``{name: DataFrame}``.
        directory: created if it doesn't exist.
        fmt: ``"csv"`` (default), ``"xlsx"`` or ``"xls"``.
        **kwargs: forwarded to :func:`save_table`.

    Returns:
        ``{name: path written}``.
    """
    target_dir = Path(directory)
    return {
        name: save_table(table, target_dir / f"{name}.{fmt.lstrip('.')}", **kwargs)
        for name, table in tables.items()
    }


def corner_report_html(
    events: pd.DataFrame,
    *,
    model=None,
    title: str = "Corner Report",
    include_figures: bool = True,
) -> str:
    """A ready-to-view HTML report for corners: team report (+ rating and
    added value if ``model`` is given), outcome breakdown and routine mix,
    with a delivery map and outcome shot map when the optional ``viz``
    extra (matplotlib/mplsoccer) is installed.

    A thin assembly of already-existing tables (:func:`~wa_setpieces.core.report.corner_report`,
    :func:`~wa_setpieces.core.rating.team_rating`,
    :func:`~wa_setpieces.core.outcomes.outcome_summary`,
    :func:`~wa_setpieces.core.routines.routine_summary`) into one portable
    HTML string via :func:`render_html_report` -- computes nothing new.
    """
    from .core.metrics import delivery_locations
    from .core.outcomes import delivery_outcomes, outcome_summary
    from .core.rating import team_rating
    from .core.report import corner_report
    from .core.routines import routine_summary

    report = corner_report(events, model=model)
    tables = {"Team report": report}
    if not report.empty:
        tables["Team rating"] = team_rating(report)
    tables["Outcome breakdown"] = outcome_summary(events, "corner")
    tables["Routine usage"] = routine_summary(events, "corner")

    figures = {}
    if include_figures:
        try:
            from .viz.plots import plot_delivery_map, plot_set_piece_outcomes
        except ImportError:
            pass  # viz extra not installed -- tables-only report is still useful
        else:
            deliveries = delivery_locations(events, "corner")
            if not deliveries.empty:
                fig, _ = plot_delivery_map(deliveries, title="Corner deliveries")
                figures["Delivery map"] = fig
            outcomes_detail = delivery_outcomes(events, "corner")
            if not outcomes_detail.empty:
                fig, _ = plot_set_piece_outcomes(outcomes_detail, title="Corner outcomes")
                figures["Outcome shot map"] = fig

    methodology = (
        "Corner-specific view built on wa_setpieces.core.report.corner_report, "
        "core.outcomes.outcome_summary and core.routines.routine_summary. "
        "Second-phase detection, retention, outcome classification and "
        "routine taxonomy are all derived heuristics -- see their module "
        "docstrings for the exact assumptions."
    )
    return render_html_report(title, tables, figures=figures or None, methodology=methodology)


def opponent_scouting_report_html(
    events: pd.DataFrame,
    opponent_id: str,
    set_piece_type: str = "corner",
    *,
    team_name: str | None = None,
    title: str | None = None,
    include_figures: bool = True,
) -> str:
    """A ready-to-view HTML report on how ``opponent_id`` *defends*
    ``set_piece_type`` -- pre-match scouting for what to expect when your
    own team attacks them, as opposed to :func:`corner_report_html`'s
    focus on a team's own attacking performance.

    Built from the conceding side (:func:`~wa_setpieces.core.defending.defensive_routine_summary`,
    :func:`~wa_setpieces.core.defending.defensive_zone_summary`,
    :func:`~wa_setpieces.core.outcomes.aerial_duel_summary`) -- which
    routines and destination zones ``opponent_id`` concedes shots/goals
    from most, and their aerial-duel record. Requires exactly two
    contestants in ``events`` (the same requirement those functions
    already have).

    Args:
        opponent_id: the ``contestantId`` to scout.
        set_piece_type: any of ``constants.SET_PIECE_TYPES`` -- aerial-duel
            record is only included for ``"corner"``/``"free_kick"`` (the
            only types :func:`~wa_setpieces.core.outcomes.aerial_duel_summary`
            supports).
        team_name: optional display name for ``opponent_id`` in the title
            and chart labels; defaults to a truncated ``opponent_id``.
    """
    from .core.defending import defensive_routine_summary, defensive_zone_summary
    from .core.outcomes import aerial_duel_summary

    label = team_name or f"{opponent_id[:8]}…"
    title = title or f"Opponent Scouting — {label} ({set_piece_type})"

    conceded_routines = defensive_routine_summary(events, set_piece_type)
    conceded_zones = defensive_zone_summary(events, set_piece_type)
    team_routines = conceded_routines[conceded_routines["contestantId"] == opponent_id].reset_index(drop=True)
    team_zones = conceded_zones[conceded_zones["contestantId"] == opponent_id].reset_index(drop=True)
    tables = {
        "Conceded by routine type": team_routines,
        "Conceded by destination zone": team_zones,
    }

    if set_piece_type in ("corner", "free_kick"):
        aerial_team, _ = aerial_duel_summary(events, set_piece_type)
        tables["Aerial duel record"] = aerial_team[aerial_team["contestantId"] == opponent_id].reset_index(drop=True)

    figures = {}
    if include_figures:
        try:
            from .viz.plots import plot_defensive_routine_bars
        except ImportError:
            pass  # viz extra not installed -- tables-only report is still useful
        else:
            if not team_routines.empty:
                fig, _ = plot_defensive_routine_bars(
                    conceded_routines, team_id=opponent_id, team_name=team_name,
                    title=f"{label} — conceded by routine type",
                )
                figures["Conceded by routine"] = fig
            if not team_zones.empty:
                fig, _ = plot_defensive_routine_bars(
                    conceded_zones, team_id=opponent_id, team_name=team_name, metric="shots_conceded",
                    title=f"{label} — shots conceded by zone",
                )
                figures["Shots conceded by zone"] = fig

    methodology = (
        "Conceding-side view built on wa_setpieces.core.defending.defensive_routine_summary, "
        "defensive_zone_summary and core.outcomes.aerial_duel_summary. "
        "Routine taxonomy, destination zones and outcome classification are "
        "all derived heuristics -- see their module docstrings for the exact "
        "assumptions."
    )
    return render_html_report(title, tables, figures=figures or None, methodology=methodology)
