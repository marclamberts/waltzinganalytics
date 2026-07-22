API reference
==============

loader
------

.. automodule:: wa_setpieces.core.loader
   :members:
   :undoc-members:
   :show-inheritance:

filters
-------

.. automodule:: wa_setpieces.core.filters
   :members:
   :undoc-members:
   :show-inheritance:

metrics
-------

.. automodule:: wa_setpieces.core.metrics
   :members:
   :undoc-members:
   :show-inheritance:

chains
------

.. automodule:: wa_setpieces.core.chains
   :members:
   :undoc-members:
   :show-inheritance:

zones
-----

.. automodule:: wa_setpieces.core.zones
   :members:
   :undoc-members:
   :show-inheritance:

phases
------

.. automodule:: wa_setpieces.core.phases
   :members:
   :undoc-members:
   :show-inheritance:

retention
---------

.. automodule:: wa_setpieces.core.retention
   :members:
   :undoc-members:
   :show-inheritance:

xt
--

.. automodule:: wa_setpieces.core.xt
   :members:
   :undoc-members:
   :show-inheritance:

value
-----

.. automodule:: wa_setpieces.core.value
   :members:
   :undoc-members:
   :show-inheritance:

outcomes
--------

.. automodule:: wa_setpieces.core.outcomes
   :members:
   :undoc-members:
   :show-inheritance:

shot_value
----------

Requires the ``ml`` extra (``pip install "wa-setpieces[ml]"``). Read the
module docstring in full before trusting the output -- several input
features are experimental best-effort defaults, not verified ground truth.

.. automodule:: wa_setpieces.ml.shot_value
   :members:
   :undoc-members:
   :show-inheritance:

report
------

.. automodule:: wa_setpieces.core.report
   :members:
   :undoc-members:
   :show-inheritance:

rating
------

.. automodule:: wa_setpieces.core.rating
   :members:
   :undoc-members:
   :show-inheritance:

workflow
--------

The whole pipeline (extraction, metrics, phases, retention, added value,
report, rating) for one set-piece type, in one call. See the "Quickstart:
one call" section on the :doc:`quickstart` page.

.. automodule:: wa_setpieces.core.workflow
   :members:
   :undoc-members:
   :show-inheritance:

providers.statsbomb
--------------------

Converts a StatsBomb open-data events export into the same internal frame
:func:`~wa_setpieces.core.loader.load_events` produces from Opta F24, so
every other module works unchanged on StatsBomb data. Read the module
docstring for exactly what is (and isn't) faithfully mapped.

.. automodule:: wa_setpieces.providers.statsbomb
   :members:
   :undoc-members:
   :show-inheritance:

viz
---

Requires the ``viz`` extra (``pip install "wa-setpieces[viz]"``). See the
:ref:`gallery` for these in action.

.. automodule:: wa_setpieces.viz.plots
   :members:
   :undoc-members:
   :show-inheritance:

theme
-----

.. automodule:: wa_setpieces.viz.theme
   :members:
   :undoc-members:
   :show-inheritance:

constants
---------

.. automodule:: wa_setpieces.core.constants
   :members:
   :undoc-members:
   :show-inheritance:

convert.corners
----------------

Requires the ``convert`` extra (``pip install "wa-setpieces[convert]"``).
Turns a directory of Opta F24 match exports plus a match-list CSV into a
flat corners table -- see the module docstring for the schema and CSV
column contract.

.. automodule:: wa_setpieces.convert.corners
   :members:
   :undoc-members:
   :show-inheritance:

cli
---

.. automodule:: wa_setpieces.cli
   :members:
   :undoc-members:
   :show-inheritance:
