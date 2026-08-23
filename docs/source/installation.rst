Installation
============

.. code-block:: bash

   pip install wa-setpieces

Want the latest unreleased changes, or to contribute? Install from
source instead:

.. code-block:: bash

   git clone https://github.com/marclamberts/waltzinganalytics.git
   cd waltzinganalytics
   pip install -e .

For the plotting helpers (:mod:`wa_setpieces.viz`, the :ref:`gallery`),
running the test suite, or building the docs:

.. code-block:: bash

   pip install -e ".[viz]"      # matplotlib, mplsoccer -- pitch plots
   pip install -e ".[ml]"       # xgboost, scikit-learn, joblib -- shot_value, cluster_routines
   pip install -e ".[convert]"  # pyarrow -- wa_setpieces.convert.corners
   pip install -e ".[xlsx]"     # openpyxl -- Excel export via save_table/save_tables
   pip install -e ".[dev]"      # pytest
   pip install -e ".[docs]"     # sphinx, sphinx-rtd-theme, sphinx-gallery, viz, ml

Requirements
------------

- Python 3.9+
- pandas >= 1.5
- matplotlib >= 3.6 and mplsoccer >= 1.2 (only for :mod:`wa_setpieces.viz.plots`;
  :mod:`wa_setpieces.viz.theme` needs matplotlib only)
- xgboost, scikit-learn, joblib (only for :mod:`wa_setpieces.ml.shot_value`;
  scikit-learn alone is also enough for
  :func:`~wa_setpieces.core.routines.cluster_routines`)
- pyarrow (only for :mod:`wa_setpieces.convert.corners`)
- openpyxl (only for Excel output from
  :func:`~wa_setpieces.save_table`/:func:`~wa_setpieces.save_tables`)

Input data
----------

``wa_setpieces`` reads three event-data providers, all through one
loading function, :func:`~wa_setpieces.load_matches` -- every call takes
the same two keywords, ``provider`` (``"opta"`` default, ``"statsbomb"``
or ``"impect"``) and ``type`` (``"match"`` default, or ``"season"`` for a
folder), so nothing else about the call changes shape between them:

- **Opta / Stats Perform** -- match event JSON exports with top-level
  ``matchDetails`` and ``event`` keys, where each event carries a
  ``typeId`` and a list of ``qualifier`` objects. This is the package's
  native format and the standard feed shape used across most
  Opta-powered football data providers.
- **StatsBomb** -- open-data-shaped events JSON exports, converted via
  :mod:`wa_setpieces.providers.statsbomb`.
- **IMPECT** -- CSV event exports, converted via
  :mod:`wa_setpieces.providers.impect`. A single IMPECT export commonly
  covers many matches already (its own ``match_id`` column), unlike
  Opta/StatsBomb's one-file-per-match convention -- see that module's
  docstring for exactly what's mapped and what isn't.

``type="season"`` accepts a folder instead of a single file -- every
``*.json`` and ``*.csv`` in it is loaded and combined into one
season-shaped events frame, ready for
:class:`~wa_setpieces.core.season.SeasonDataset`. The file extension
never gates which provider a file is tried against -- ``provider``
alone decides that -- so a folder can mix extensions freely; a file
that doesn't parse under the chosen ``provider`` (wrong shape, or a
non-event sidecar file like StatsBomb's own ``matches.json``) is
skipped with a warning rather than aborting the whole folder. Passing a
directory with ``type="match"`` (or a single file with ``type="season"``) raises
``ValueError`` rather than silently doing the other thing.

Each provider also accepts either extension on a single file, not just
the folder scan: any of the three loaders will read a ``.csv`` or
``.json`` file of a previously-exported events frame in its own
internal shape (e.g. ``events.to_csv(...)`` or ``events.to_json(...)``
from an earlier run, reloaded later) round-trip safe -- so a match
already converted once doesn't need to be re-converted from its
original native format just because you saved it under the other
extension.
