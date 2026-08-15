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
