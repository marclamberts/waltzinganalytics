"""Convert raw Opta F24 event exports into flat tables other tools expect.

See :mod:`wa_setpieces.convert.corners` for the corners-delivery converter.
"""

from .corners import build_corners_dataset, convert_to_parquet

__all__ = ["build_corners_dataset", "convert_to_parquet"]
