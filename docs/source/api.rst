API reference
==============

loader
------

.. automodule:: wa_setpieces.core.loader
   :members:
   :undoc-members:
   :show-inheritance:

constants
---------

.. automodule:: wa_setpieces.core.constants
   :members:
   :undoc-members:
   :show-inheritance:

schema
------

The provider-neutral event contract every other module assumes --
:func:`~wa_setpieces.validate_events` checks it,
:func:`~wa_setpieces.event_capabilities` reports which optional fields an
adapter supplies.

.. automodule:: wa_setpieces.core.schema
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

routines
--------

Rule-based routine taxonomy (``restart_routines``, including
``delivery_technique``/``post_target``), a data-driven k-means
alternative (``cluster_routines``/``cluster_summary``, optional ``ml``
extra), team/taker tactical profiles, and long-throw specialist
detection.

.. automodule:: wa_setpieces.core.routines
   :members:
   :undoc-members:
   :show-inheritance:

attribution
-----------

Event-sequence-based player attribution after a delivery -- explicitly
labelled ``"event_sequence"`` confidence, since event data cannot prove
physical contact the way tracking data can.

.. automodule:: wa_setpieces.core.attribution
   :members:
   :undoc-members:
   :show-inheritance:

placement
---------

Shared goal-mouth shot placement geometry (qualifiers 102/103), used by
both :mod:`wa_setpieces.ml.shot_value` and
:mod:`wa_setpieces.core.penalties`. Pure qualifier math -- no optional
dependency needed.

.. automodule:: wa_setpieces.core.placement
   :members:
   :undoc-members:
   :show-inheritance:

penalties
---------

.. automodule:: wa_setpieces.core.penalties
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

defending
---------

.. automodule:: wa_setpieces.core.defending
   :members:
   :undoc-members:
   :show-inheritance:

season
------

Match-safe multi-match aggregation and rolling attacking/defensive form.

.. automodule:: wa_setpieces.core.season
   :members:
   :undoc-members:
   :show-inheritance:

workflow
--------

The whole pipeline (extraction, metrics, phases, retention, added value,
report, rating, defending, routine clusters, aerial duels, penalties,
long throws) for one set-piece type, in one call. See "The whole
pipeline in one call" on the :doc:`quickstart` page.

.. automodule:: wa_setpieces.core.workflow
   :members:
   :undoc-members:
   :show-inheritance:

clips
-----

Video-clip in/out timestamp windows for deliveries, for handing off to a
video-clipping tool.

.. automodule:: wa_setpieces.core.clips
   :members:
   :undoc-members:
   :show-inheritance:

reporting
---------

Self-contained HTML reports (``corner_report_html``,
``opponent_scouting_report_html``, ``render_html_report``,
``write_html_report``) and CSV/Excel export (``save_table``,
``save_tables`` -- Excel needs the optional ``xlsx`` extra).

.. automodule:: wa_setpieces.reporting
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
