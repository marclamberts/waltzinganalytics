"""Adapters that convert other providers' event feeds into the internal
events DataFrame :func:`wa_setpieces.core.loader.load_events` produces from
Opta F24, so the rest of the package works unchanged regardless of source.

Currently: :mod:`wa_setpieces.providers.statsbomb` (StatsBomb open data).
Opta F24 needs no adapter -- it's the package's native format, handled
directly by :mod:`wa_setpieces.core.loader`.

Impect is not supported here: it's a closed, proprietary feed with no
public schema to build and verify an adapter against. Contributing one
needs a real sample export (or an official schema reference) to check
qualifier/coordinate mapping against, the same way this module's StatsBomb
mapping and the Opta constants in :mod:`wa_setpieces.core.constants` were
verified against real exports (see that module's docstring).
"""

from .statsbomb import load_statsbomb_events

__all__ = ["load_statsbomb_events"]
