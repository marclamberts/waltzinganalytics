"""Pitch and chart visualizations (:mod:`wa_setpieces.viz.plots`) plus the
shared dark/light color palette (:mod:`wa_setpieces.viz.theme`).

``wa_setpieces.viz.theme`` only needs matplotlib. ``wa_setpieces.viz.plots``
additionally needs mplsoccer -- this package intentionally does not import
either submodule eagerly, so ``from wa_setpieces.viz import theme`` stays
usable without mplsoccer installed. Requires the optional ``viz`` extra:
``pip install "wa-setpieces[viz]"``.
"""
