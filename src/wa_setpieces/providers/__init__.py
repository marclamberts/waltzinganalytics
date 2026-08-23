"""Per-provider converters that turn another provider's event feed into
the internal events DataFrame :func:`wa_setpieces.core.loader.load_events`
produces from Opta's native format, so the rest of the package works
unchanged regardless of source.

Currently: :mod:`wa_setpieces.providers.statsbomb` (StatsBomb open data)
and :mod:`wa_setpieces.providers.impect` (IMPECT event exports). Opta
needs no converter -- it's the package's native format, handled directly
by :mod:`wa_setpieces.core.loader`.

Most code should not import from here directly. Use
:func:`wa_setpieces.core.loader.load_matches` with ``provider="opta"``/
``"statsbomb"``/``"impect"`` instead -- one function, one ``provider``
argument, works on a single file or a whole folder either way. The
functions in this subpackage are what it dispatches to internally.
"""

from .impect import load_impect_events
from .statsbomb import load_statsbomb_events

__all__ = ["load_statsbomb_events", "load_impect_events"]
