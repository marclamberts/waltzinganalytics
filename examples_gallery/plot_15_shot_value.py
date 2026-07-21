"""
Shot value (experimental)
============================

.. warning::
   Read :mod:`wa_setpieces.ml.shot_value`'s module docstring in full before
   trusting this output for anything real. The five bundled models were
   trained elsewhere against a feature schema this package has to
   reconstruct from Opta F24 qualifiers -- some inputs are confidently
   derived, several are experimental best-effort defaults (documented in
   the module docstring), not verified ground truth.

Five pre-trained gradient-boosted models, bundled with the ``ml`` extra,
score every shot in a match: P(on target), xG On Target (P(goal) given
on target), Post-Shot xG (P(goal) from actual placement), a situational
signal, and a 4-class outcome distribution. :func:`~wa_setpieces.ml.shot_value.shot_value`
runs all five and blends ``psxg`` and ``on_target_prob * xgot`` -- two
independent P(goal) estimates -- into one ``shot_value`` column.
"""

from pathlib import Path

from wa_setpieces import load_events
from wa_setpieces.ml.shot_value import ShotValueModels, shot_value

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

match = load_events(DATA)

# %%
# Load once, reuse across matches (the .pkl files are a few hundred KB
# each and slower to load than to run inference with):
models = ShotValueModels.load()
shots = shot_value(match.events, models)
shots[["eventId", "playerName", "is_goal", "set_piece_type", "on_target_prob", "xgot", "psxg", "shot_value"]]

# %%
# Set-piece shots specifically, ranked by blended shot value:
set_piece_shots = shots[shots["set_piece_type"].notna()].sort_values("shot_value", ascending=False)
set_piece_shots[["playerName", "set_piece_type", "on_target_prob", "psxg", "shot_value"]]
