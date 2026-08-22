Reports, export and the command line
=======================================

Every table this guide has produced so far needs to leave Python at some
point -- into a CSV for someone else's pipeline, an Excel file for a
coach, or a self-contained HTML report someone can open without pandas
installed. This page covers all three, plus the command-line interface
that wraps most of this guide for people who'd rather not write Python
at all.

Self-contained HTML reports
-------------------------------

:func:`~wa_setpieces.corner_report_html` (attacking) and
:func:`~wa_setpieces.opponent_scouting_report_html` (conceding, see
:doc:`defending_and_season`) render tables plus delivery/shot maps --
when the ``viz`` extra is installed -- into one portable HTML string,
degrading gracefully to tables-only otherwise:

.. code-block:: python

   from pathlib import Path
   from wa_setpieces import corner_report_html

   html = corner_report_html(match.events, model=model)  # a ready-to-write HTML string
   Path("corner_report.html").write_text(html, encoding="utf-8")

CSV and Excel export
------------------------

Any table this package produces can be saved to CSV or Excel, chosen by
file extension:

.. code-block:: bash

   pip install -e ".[xlsx]"   # openpyxl, for .xlsx/.xls output

.. code-block:: python

   import pandas as pd
   from wa_setpieces import save_table, save_tables

   save_table(corner_report(match.events, model=model), "corner_report.xlsx")

   # One file per SetPieceWorkflow table (skip the non-table fields, e.g. set_piece_type):
   tables = {name: value for name, value in vars(result).items() if isinstance(value, pd.DataFrame)}
   save_tables(tables, "workflow_tables/", fmt="csv")

Command line
---------------

The simplest form -- a summary, straight to a CSV or the terminal:

.. code-block:: bash

   wa-setpieces match.json
   wa-setpieces match.json --csv summary.csv

Past that, the CLI exposes the same functions this whole guide has been
walking through:

.. code-block:: bash

   wa-setpieces summary match.json --output summary.json --format json
   wa-setpieces train-xt season/*.json --output league-model.npz
   wa-setpieces workflow match.json --type corner --model league-model.npz --output tables/ --format xlsx
   wa-setpieces report match.json --type corner --model league-model.npz --output report.html
   wa-setpieces scout match.json --opponent <contestantId> --type corner --output scouting.html
   wa-setpieces season match_1.json match_2.json ... --action season-report --type corner --output season.csv

- ``workflow`` exports every table :func:`~wa_setpieces.run_workflow`
  produces -- including the defensive, routine-cluster, aerial-duel,
  penalty and long-throw tables -- as one CSV (default) or Excel
  (``--format xlsx``) file per table, no extra flags needed.
- ``report --type corner`` writes the curated report above (rating,
  outcome/routine breakdowns, delivery/outcome maps if ``viz`` is
  installed); other ``--type``\\ s fall back to a generic dump of every
  workflow table, since there's no equivalent curated report for them
  yet -- see :doc:`../categories`.
- ``scout`` and ``season`` put
  :func:`~wa_setpieces.opponent_scouting_report_html` and
  :class:`~wa_setpieces.SeasonDataset` on the command line; see
  :doc:`defending_and_season` for both.
- Use ``--provider statsbomb`` with any command for a StatsBomb events
  export.
- Outputs support CSV, JSON and Parquet where applicable; for CSV or
  Excel from Python directly, use ``save_table``/``save_tables`` above.

``season``'s ``--action`` is one of ``summary``, ``report``
(match-level rows), ``season-report`` (whole-season roll-up), ``rolling``
or ``rolling-defense`` (``--window`` trailing matches). Each input file is
tagged with its own filename as ``matchId``, so distinct filenames are
required -- the same ``matchId`` uniqueness guarantee covered in
:doc:`defending_and_season`.
