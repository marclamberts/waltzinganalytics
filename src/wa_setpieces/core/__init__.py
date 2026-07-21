"""Core set-piece extraction and analytics: loading Opta F24 events, tagging
set pieces, second phases, retention, xT and added-value scoring.

These modules have no dependencies beyond pandas/numpy and are imported
eagerly by :mod:`wa_setpieces` -- unlike :mod:`wa_setpieces.viz` (needs the
``viz`` extra) and :mod:`wa_setpieces.ml` (needs the ``ml`` extra).
"""
