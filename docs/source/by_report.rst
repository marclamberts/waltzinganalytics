.. _by-report:

By report and export
========================

The same pick-one-see-what-it-does reference :doc:`categories` gives set
pieces, for getting a result out of Python -- a portable HTML report, a
CSV/Excel file, or straight off the command line.

Self-contained HTML reports
--------------------------------

**What it produces**
   A single, portable HTML string -- tables plus delivery/shot maps if
   the ``viz`` extra is installed, degrading gracefully to tables-only
   otherwise. Open it in a browser, no pandas or Python needed on the
   other end.

**Requirements**
   :func:`~wa_setpieces.corner_report_html` works on ``corner`` events
   directly; :func:`~wa_setpieces.opponent_scouting_report_html` needs
   an ``opponent_id`` and a ``set_piece_type``. Both accept an optional
   fitted model for richer output.

**Compute it**

.. code-block:: python

   from pathlib import Path
   from wa_setpieces import corner_report_html, opponent_scouting_report_html

   html = corner_report_html(match.events, model=model)
   Path("corner_report.html").write_text(html, encoding="utf-8")

   scouting = opponent_scouting_report_html(
       match.events, opponent_id="...", set_piece_type="corner", team_name="Rivals FC",
   )
   Path("scouting.html").write_text(scouting, encoding="utf-8")

**Where it's used**
   ``corner_report_html`` is corner's curated report in :doc:`categories`
   -- the only type with a bespoke layout; every other type falls back to
   a generic table dump. ``opponent_scouting_report_html`` is the
   conceding-side, defensive mirror of the same idea.

CSV and Excel export
-------------------------

**What it produces**
   Any table this package returns, saved to disk -- one table to one
   file, or a whole dict of tables (e.g. a
   :class:`~wa_setpieces.core.workflow.SetPieceWorkflow`'s fields) to one
   file per table in a directory.

**Requirements**
   ``.xlsx``/``.xls`` output needs the ``xlsx`` extra
   (``pip install -e ".[xlsx]"``, openpyxl); ``.csv`` needs nothing extra.

**Compute it**

.. code-block:: python

   import pandas as pd
   from wa_setpieces import save_table, save_tables, corner_report

   save_table(corner_report(match.events, model=model), "corner_report.xlsx")

   tables = {name: value for name, value in vars(result).items() if isinstance(value, pd.DataFrame)}
   save_tables(tables, "workflow_tables/", fmt="csv")

**Where it's used**
   Every "Export to CSV/Excel" entry in :doc:`categories`.

Command line
----------------

**What it produces**
   The same functions above, without writing Python -- summaries,
   full-workflow table dumps, curated reports, opponent scouting,
   season aggregation, and xT model training.

**Requirements**
   The ``wa-setpieces`` console script (installed with the package).
   ``--provider {opta,statsbomb,impect}`` on any command switches the
   input format (default ``opta``). Every command's file argument also
   accepts a folder -- every match file in it is loaded and combined,
   the same way :func:`~wa_setpieces.load_matches` does.

**Compute it**

.. code-block:: bash

   wa-setpieces match.json --csv summary.csv
   wa-setpieces workflow match.json --type corner --model league-model.npz --output tables/ --format xlsx
   wa-setpieces report match.json --type corner --model league-model.npz --output report.html
   wa-setpieces scout match.json --opponent <contestantId> --type corner --output scouting.html
   wa-setpieces summary season_2024/ --provider statsbomb --output season_summary.csv
   wa-setpieces summary impect_export.csv --provider impect --output season_summary.csv
   wa-setpieces season match_1.json match_2.json --action season-report --type corner --output season.csv
   wa-setpieces train-xt season/*.json --output league-model.npz

**Where it's used**
   Every "Export to CSV/Excel" ``wa-setpieces workflow`` command in
   :doc:`categories` is this same CLI.
