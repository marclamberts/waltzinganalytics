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
