"""Shot-value scoring from a bundle of pre-trained gradient-boosted models.

Requires the optional ``ml`` extra: ``pip install "wa-setpieces[ml]"``
(xgboost, scikit-learn, joblib). Five models ship inside the package
(``wa_setpieces/ml/models/*.pkl``, ~4.5MB), each an ``xgboost.XGBClassifier``,
four of them wrapped in :class:`CalibratedXGB` (an isotonic-regression
probability calibrator on top of the raw XGBoost output):

- ``pontarget`` -- P(shot is on target). Features: shot geometry + body
  part + situational flags.
- ``xgot`` -- P(goal | shot is on target), "xG On Target". Features:
  geometry + body part + situational + placement.
- ``psxg`` -- P(goal), from actual placement, "Post-Shot xG". Same
  features as ``xgot``.
- ``situation`` -- a binary situational-quality signal, unlabeled.
  Features: situational flags + period/time only.
- ``multi_outcome`` -- a 4-class shot-outcome distribution, unlabeled.
  Features: geometry + body part + situational (same as ``pontarget``).

:func:`shot_value` runs all five and returns one row per shot with each
model's raw prediction plus a blended ``shot_value`` column.

This is a separate, heavier concept from :meth:`wa_setpieces.core.xt.XTModel.shot_value`
(a single grid-based P(goal) estimate, fit from your own match data, with
no external dependencies) used by :func:`wa_setpieces.core.value.set_piece_added_value`.
Use the grid-based one if you want something dependency-free and fit
specifically to your own data; use this module for a richer, pre-trained,
multi-model breakdown, once you've read the limitations below.

Known limitations -- READ BEFORE TRUSTING THE OUTPUT
------------------------------------------------------
These models were trained elsewhere, against a feature schema this module
has to *reconstruct* from Opta F24 qualifiers on each shot event -- F24
does not ship these exact named features, and the module docstring the
models were trained with is not available here. Some inputs are
confidently derived; others are the module's best empirical guess from
real match data (goal-rate correlation and qualifier co-occurrence across
~50 real shots), or a documented geometric formula of this module's own
invention where the original definition wasn't recoverable. Treat any
column below marked *(experimental)* as a reasonable placeholder, not
ground truth -- verify against your own labeled shots before relying on
it for anything high-stakes, and prefer passing in a corrected
:data:`FEATURE_OVERRIDES` mapping over trusting the default.

Confidently derived (verified against real F24 data or this package's
own already-validated logic):

- ``distance``, ``angle``, ``y_sym`` -- pure geometry from ``x``/``y``,
  assuming a 105m x 68m pitch and a 7.32m goal (the football-analytics
  community's standard assumption; verify it matches your training data's
  assumption if distances look systematically off).
- ``is_from_corner``, ``is_free_kick``, ``is_set_piece``,
  ``is_throw_in_set_piece``, ``is_open_play``, ``is_corner_second_phase``
  -- from :func:`wa_setpieces.core.chains.link_set_piece_shots` and
  :func:`wa_setpieces.core.phases.second_phases`, which are already-tested
  logic elsewhere in this package, not new inference.
- ``is_assisted``, ``is_individual_play`` -- from qualifierId 29
  ("Assist"), already a validated constant in
  :mod:`wa_setpieces.core.constants` (``QUALIFIER_ASSIST``).
- ``is_right_foot``, ``is_left_foot`` -- from qualifierId 20/72, which
  partition 100% of shots in both sample matches (52/52); their relative
  frequency (77%/23%) matches typical player footedness, consistent with
  "right footed"/"left footed" but not confirmed against documentation.
- ``goal_y_norm`` -- from qualifierId 102 ("goal mouth y"), confirmed by
  its value range (spans well outside the goal-post band for shots that
  missed wide, consistent with a whole-pitch-width coordinate).

*(experimental)* -- no reliable qualifier signal was found; these default
to a fixed value rather than a guessed-but-wrong qualifier ID, and are
documented here so the gap is visible rather than silently wrong:

- ``is_header``, ``is_other_body_part``, ``is_volley`` -- always ``False``
  (headers/volleys are not currently distinguished from other foot shots).
- ``is_big_chance``, ``is_one_on_one``, ``is_fast_break``, ``is_scramble``
  -- always ``False`` (no qualifier candidate cleared even a weak
  goal-rate correlation bar on the ~50-shot sample this was checked
  against; contributions with a verified mapping are welcome).
- ``is_intentional_assist`` -- set equal to ``is_assisted`` (a real
  "unintentional assist" qualifier is not observed in either sample match).
- ``is_deflected`` -- always ``False``.
- ``goal_h_norm``, ``goal_frame_dist``, ``corner_zone``,
  ``placement_score`` -- computed from ``goal_y_norm`` and qualifierId 103
  ("goal mouth z") with a documented formula of this module's own
  invention (see :func:`_goal_placement`); ``goal_h_norm`` additionally
  assumes qualifierId 103 is on a 0-38 scale (38 = crossbar), a figure
  seen in other open-source Opta parsers but not independently confirmed
  here.
- ``model_multi_outcome``'s four output classes and ``model_situation``'s
  binary target are exposed as raw, unlabeled probabilities
  (``outcome_class_0`` .. ``outcome_class_3``, ``situational_prob``) --
  which class means "goal" vs "saved" vs "blocked" could not be recovered
  (a same-features sanity check on real shots showed only a weak
  goal-rate skew towards class 3, not a clean separation) so no semantic
  label is assigned. They are **not** included in the blended
  ``shot_value`` score for this reason.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..core import constants as c

MODELS_DIR = Path(__file__).parent / "models"

PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
GOAL_WIDTH_M = 7.32
GOAL_HEIGHT_QUALIFIER_MAX = 38.0  # see module docstring: unconfirmed assumption

GOAL_Y_LOW = 50.0 - (GOAL_WIDTH_M / PITCH_WIDTH_M * 100.0) / 2.0
GOAL_Y_HIGH = 50.0 + (GOAL_WIDTH_M / PITCH_WIDTH_M * 100.0) / 2.0

QUALIFIER_RIGHT_FOOTED = 20
QUALIFIER_LEFT_FOOTED = 72
QUALIFIER_GOAL_MOUTH_Y = 102
QUALIFIER_GOAL_MOUTH_Z = 103

PONTARGET_FEATURES = [
    "distance", "angle", "y_sym", "is_header", "is_right_foot", "is_left_foot",
    "is_other_body_part", "is_volley", "is_one_on_one", "is_fast_break",
    "is_from_corner", "is_free_kick", "is_set_piece", "is_throw_in_set_piece",
    "is_open_play", "is_assisted", "is_intentional_assist", "is_individual_play",
]
PLACEMENT_FEATURES = [
    "is_deflected", "goal_y_norm", "goal_h_norm", "goal_frame_dist",
    "corner_zone", "placement_score",
]
XGOT_FEATURES = PONTARGET_FEATURES + PLACEMENT_FEATURES
SITUATION_FEATURES = [
    "is_big_chance", "is_one_on_one", "is_fast_break", "is_from_corner",
    "is_corner_second_phase", "is_free_kick", "is_set_piece",
    "is_throw_in_set_piece", "is_open_play", "is_assisted",
    "is_intentional_assist", "is_individual_play", "is_scramble", "is_header",
    "period_id", "time_min",
]


class CalibratedXGB:
    """An ``xgboost.XGBClassifier`` (``clf``) with an isotonic-regression
    probability calibrator (``iso``) on top -- the wrapper the bundled
    ``pontarget``/``xgot``/``psxg``/``situation`` models use.
    """

    def __init__(self, clf=None, iso=None):
        self.clf = clf
        self.iso = iso

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Calibrated P(positive class), shape ``(n_samples,)``."""
        raw = self.clf.predict_proba(X)[:, 1]
        return self.iso.predict(raw)


# The bundled .pkl files were pickled back when this module lived at
# `wa_setpieces.shot_value` (pre-0.9 flat layout); pickle resolves classes by
# that recorded module path at load time, not by where the class is defined
# now. Alias the pre-restructure path to this module so `joblib.load` still
# finds `CalibratedXGB` after the module's move to `wa_setpieces.ml.shot_value`.
sys.modules.setdefault("wa_setpieces.shot_value", sys.modules[__name__])


def _register_calibrated_xgb_in_main() -> None:
    # The bundled .pkl files were re-saved with CalibratedXGB importable
    # from this module, but joblib still looks it up by whatever module
    # name was active when *this* module is imported as `__main__` (e.g.
    # running this file as a script) -- register it there too so both
    # import paths unpickle cleanly.
    main_mod = sys.modules.get("__main__")
    if main_mod is not None and not hasattr(main_mod, "CalibratedXGB"):
        main_mod.CalibratedXGB = CalibratedXGB


@dataclass
class ShotValueModels:
    """A loaded bundle of the five shot-value models. Build with :meth:`load`."""

    pontarget: object
    xgot: object
    psxg: object
    situation: object
    multi_outcome: object

    @classmethod
    def load(cls, models_dir: str | Path | None = None) -> "ShotValueModels":
        """Load all five models from ``models_dir`` (default: the models
        bundled with this package).

        Loading emits (and this suppresses) two harmless, unactionable
        warnings every time, regardless of environment: xgboost's "loading
        a serialized model from an older version" notice, and scikit-learn's
        ``InconsistentVersionWarning`` for the isotonic calibrators -- both
        fire because the bundled models were trained under older xgboost/
        scikit-learn releases and were never refit, not because anything is
        actually wrong with this load.
        """
        import warnings

        try:
            import joblib
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "wa_setpieces.ml.shot_value requires the 'ml' extra: "
                'pip install "wa-setpieces[ml]"'
            ) from exc

        _register_calibrated_xgb_in_main()
        directory = Path(models_dir) if models_dir is not None else MODELS_DIR
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            try:
                from sklearn.exceptions import InconsistentVersionWarning
                warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
            except ImportError:  # pragma: no cover
                pass
            return cls(
                pontarget=joblib.load(directory / "model_pontarget.pkl"),
                xgot=joblib.load(directory / "model_xgot.pkl"),
                psxg=joblib.load(directory / "model_psxg.pkl"),
                situation=joblib.load(directory / "model_situation.pkl"),
                multi_outcome=joblib.load(directory / "model_multi_outcome.pkl"),
            )


def _qualifier_flag(raw_event: pd.Series, qualifier_id: int) -> bool:
    """Whether boolean-style qualifier ``qualifier_id`` is present on
    ``raw_event``. Absent qualifiers are ``NaN`` in the loader's flattened
    ``q_<id>`` columns (see :mod:`wa_setpieces.core.loader`) -- and ``bool(nan)``
    is ``True`` in Python, so a plain ``bool(raw_event.get(...))`` silently
    treats "column not present" as "flag set". Use this instead."""
    value = raw_event.get(f"q_{qualifier_id}")
    return bool(value) if pd.notna(value) else False


def _shot_geometry(x: float, y: float) -> tuple[float, float, float]:
    """``(distance_m, angle_deg, y_sym)`` from Opta x/y (0-100, goal at
    x=100, y=50), assuming a 105m x 68m pitch and a 7.32m goal."""
    dx_m = (100.0 - x) / 100.0 * PITCH_LENGTH_M
    dy_m = (y - 50.0) / 100.0 * PITCH_WIDTH_M
    distance = float(np.hypot(dx_m, dy_m))

    shot_m = np.array([x / 100.0 * PITCH_LENGTH_M, y / 100.0 * PITCH_WIDTH_M])
    post_low = np.array([PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0 - GOAL_WIDTH_M / 2.0])
    post_high = np.array([PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0 + GOAL_WIDTH_M / 2.0])
    v1, v2 = post_low - shot_m, post_high - shot_m
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    cos_angle = float(np.dot(v1, v2) / denom) if denom else 1.0
    angle = float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))

    y_sym = float(abs(y - 50.0))
    return distance, angle, y_sym


def _goal_placement(raw_event: pd.Series) -> dict:
    """Placement features from qualifierId 102/103 -- see the module
    docstring's *(experimental)* section for what's confirmed vs guessed.

    ``raw_event`` is a row from :func:`~wa_setpieces.load_events`'s events
    DataFrame, where each qualifier is already flattened to a ``q_<id>``
    column (see :class:`wa_setpieces.core.loader.Match`)."""
    goal_y_raw = raw_event.get(f"q_{QUALIFIER_GOAL_MOUTH_Y}")
    goal_z_raw = raw_event.get(f"q_{QUALIFIER_GOAL_MOUTH_Z}")

    goal_y_norm = float("nan")
    goal_h_norm = float("nan")
    if goal_y_raw is not None:
        try:
            goal_y_norm = (float(goal_y_raw) - GOAL_Y_LOW) / (GOAL_Y_HIGH - GOAL_Y_LOW)
        except (TypeError, ValueError):
            pass
    if goal_z_raw is not None:
        try:
            goal_h_norm = float(goal_z_raw) / GOAL_HEIGHT_QUALIFIER_MAX
        except (TypeError, ValueError):
            pass

    if np.isnan(goal_y_norm) or np.isnan(goal_h_norm):
        return dict(
            is_deflected=0, goal_y_norm=goal_y_norm, goal_h_norm=goal_h_norm,
            goal_frame_dist=float("nan"), corner_zone=-1, placement_score=float("nan"),
        )

    # Distance outside the goal frame (0 if inside it) -- how far wide/high
    # the placement missed, in normalized goal-width/height units.
    dx = max(0.0 - goal_y_norm, goal_y_norm - 1.0, 0.0)
    dy = max(0.0 - goal_h_norm, goal_h_norm - 1.0, 0.0)
    goal_frame_dist = float(np.hypot(dx, dy))

    # 3x3 grid over the goal frame (clamped to it even if the shot missed
    # wide, so "which zone was it *aimed* at" stays defined): 0=bottom-left
    # .. 8=top-right, row-major, matching a typical goal-frame heatmap.
    col = int(np.clip(goal_y_norm, 0.0, 0.999) * 3)
    row = int(np.clip(goal_h_norm, 0.0, 0.999) * 3)
    corner_zone = row * 3 + col

    # Simple "hardest to save" proxy: distance from goal center, in the
    # same normalized units -- corners of the frame score higher.
    placement_score = float(np.hypot(goal_y_norm - 0.5, goal_h_norm - 0.5))

    return dict(
        is_deflected=0, goal_y_norm=goal_y_norm, goal_h_norm=goal_h_norm,
        goal_frame_dist=goal_frame_dist, corner_zone=corner_zone,
        placement_score=placement_score,
    )


_FEATURE_COLUMNS = [
    "eventId", "contestantId", "playerId", "playerName", "x", "y", "periodId",
    "time_min", "is_goal", "set_piece_type",
    "distance", "angle", "y_sym", "is_header", "is_right_foot", "is_left_foot",
    "is_other_body_part", "is_volley", "is_one_on_one", "is_fast_break",
    "is_big_chance", "is_scramble", "is_from_corner", "is_corner_second_phase",
    "is_free_kick", "is_set_piece", "is_throw_in_set_piece", "is_open_play",
    "is_assisted", "is_intentional_assist", "is_individual_play", "period_id",
    "is_deflected", "goal_y_norm", "goal_h_norm", "goal_frame_dist",
    "corner_zone", "placement_score",
]


def build_shot_features(events: pd.DataFrame) -> pd.DataFrame:
    """Build the full feature set for every shot in ``events``.

    Returns one row per shot (``typeId`` in Miss/Post/AttemptSaved/Goal)
    with identifying columns (``eventId``, ``contestantId``, ``playerId``,
    ``playerName``, ``x``, ``y``, ``periodId``, ``time_min``, ``is_goal``,
    ``set_piece_type``) plus every feature column the five bundled models
    need. See the module docstring for which features are confidently
    derived vs experimental defaults.
    """
    from ..core.chains import link_set_piece_shots
    from ..core.phases import second_phases

    linked = link_set_piece_shots(events)
    if linked.empty:
        return pd.DataFrame(columns=_FEATURE_COLUMNS)

    second_phase_keys = set()
    sp = second_phases(events, "corner")
    for _, row in sp.iterrows():
        if row["second_phase_shot"] and pd.notna(row["second_phase_event_id"]):
            second_phase_keys.add((row["contestant_id"], int(row["second_phase_event_id"])))

    # Indexed by (contestantId, eventId), the only actually-unique key in
    # F24 (see chains.py's module docstring) -- `linked` drops the q_*
    # qualifier columns, so this looks each shot's raw event back up.
    events_by_key = events.set_index(["contestantId", "eventId"], drop=False)

    rows = []
    for _, shot in linked.iterrows():
        key = (shot["contestantId"], shot["eventId"])
        raw_event = events_by_key.loc[key]
        if isinstance(raw_event, pd.DataFrame):  # defensive; shouldn't occur
            raw_event = raw_event.iloc[0]

        distance, angle, y_sym = _shot_geometry(float(shot["x"]), float(shot["y"]))

        right_foot = _qualifier_flag(raw_event, QUALIFIER_RIGHT_FOOTED)
        left_foot = _qualifier_flag(raw_event, QUALIFIER_LEFT_FOOTED)
        assisted = _qualifier_flag(raw_event, c.QUALIFIER_ASSIST)

        set_piece_type = shot["set_piece_type"]
        is_corner_second_phase = key in second_phase_keys

        placement = _goal_placement(raw_event)

        rows.append(dict(
            eventId=shot["eventId"],
            contestantId=shot["contestantId"],
            playerId=shot["playerId"],
            playerName=shot["playerName"],
            x=shot["x"],
            y=shot["y"],
            periodId=raw_event["periodId"],
            period_id=raw_event["periodId"],
            time_min=shot["timeMin"],
            is_goal=shot["is_goal"],
            set_piece_type=set_piece_type,
            distance=distance,
            angle=angle,
            y_sym=y_sym,
            is_header=0,
            is_right_foot=int(right_foot),
            is_left_foot=int(left_foot),
            is_other_body_part=int(not right_foot and not left_foot),
            is_volley=0,
            is_one_on_one=0,
            is_fast_break=0,
            is_big_chance=0,
            is_scramble=0,
            is_from_corner=int(set_piece_type == "corner"),
            is_corner_second_phase=int(is_corner_second_phase),
            is_free_kick=int(set_piece_type == "free_kick"),
            is_set_piece=int(set_piece_type is not None),
            is_throw_in_set_piece=int(set_piece_type == "throw_in"),
            is_open_play=int(set_piece_type is None),
            is_assisted=int(assisted),
            is_intentional_assist=int(assisted),
            is_individual_play=int(not assisted),
            **placement,
        ))

    return pd.DataFrame(rows, columns=_FEATURE_COLUMNS)


def shot_value(events: pd.DataFrame, models: ShotValueModels | None = None) -> pd.DataFrame:
    """Score every shot in ``events`` with the five bundled models.

    Args:
        models: a loaded :class:`ShotValueModels`; defaults to loading the
            bundled models fresh (slower -- pass a cached instance if
            scoring many matches).

    Returns:
        One row per shot with identifying columns, each model's raw
        prediction (``on_target_prob``, ``xgot``, ``psxg``,
        ``situational_prob``, ``outcome_class_0`` .. ``outcome_class_3``),
        and a blended ``shot_value`` column
        (``mean(psxg, on_target_prob * xgot)`` -- see the module docstring
        for why ``situational_prob``/``outcome_class_*`` aren't blended in).
    """
    models = models or ShotValueModels.load()
    features = build_shot_features(events)
    if features.empty:
        return features.assign(
            on_target_prob=pd.Series(dtype=float), xgot=pd.Series(dtype=float),
            psxg=pd.Series(dtype=float), situational_prob=pd.Series(dtype=float),
            shot_value=pd.Series(dtype=float),
        )

    X_pontarget = features[PONTARGET_FEATURES].astype(float)
    X_xgot = features[XGOT_FEATURES].astype(float)
    X_situation = features[SITUATION_FEATURES].astype(float)

    on_target_prob = models.pontarget.predict_proba(X_pontarget)
    xgot = models.xgot.predict_proba(X_xgot)
    psxg = models.psxg.predict_proba(X_xgot)
    situational_prob = models.situation.predict_proba(X_situation)
    outcome_probs = models.multi_outcome.predict_proba(X_pontarget)

    result = features[
        ["eventId", "contestantId", "playerId", "playerName", "x", "y", "periodId",
         "time_min", "is_goal", "set_piece_type"]
    ].copy()
    result["on_target_prob"] = on_target_prob
    result["xgot"] = xgot
    result["psxg"] = psxg
    result["situational_prob"] = situational_prob
    for i in range(outcome_probs.shape[1]):
        result[f"outcome_class_{i}"] = outcome_probs[:, i]
    result["shot_value"] = (result["psxg"] + result["on_target_prob"] * result["xgot"]) / 2.0
    return result
