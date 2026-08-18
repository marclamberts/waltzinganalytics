"""Safe multi-match analysis for seasons and competitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .defending import defensive_set_piece_summary
from .loader import load_events_multi
from .metrics import set_piece_summary
from .report import set_piece_report
from .schema import validate_events


@dataclass
class SeasonDataset:
    """A validated multi-match event collection with match-safe aggregations."""

    events: pd.DataFrame
    metadata: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self) -> None:
        validate_events(self.events, require_match_id=True)
        self.events = self.events.copy()
        self.events["matchId"] = self.events["matchId"].astype(str)
        if not self.metadata.empty:
            if "matchId" not in self.metadata:
                raise ValueError("metadata must contain a matchId column")
            self.metadata = self.metadata.copy()
            self.metadata["matchId"] = self.metadata["matchId"].astype(str)

    @classmethod
    def from_sources(
        cls,
        sources: Iterable[str | Path | dict[str, Any]],
        *,
        match_ids: Iterable[str] | None = None,
        metadata: pd.DataFrame | None = None,
    ) -> "SeasonDataset":
        source_list = list(sources)
        ids = list(match_ids) if match_ids is not None else None
        return cls(load_events_multi(source_list, ids), metadata if metadata is not None else pd.DataFrame())

    @property
    def match_ids(self) -> list[str]:
        return self.events["matchId"].drop_duplicates().tolist()

    def iter_matches(self):
        for match_id, frame in self.events.groupby("matchId", sort=False):
            yield match_id, frame.reset_index(drop=True)

    def summary(self) -> pd.DataFrame:
        frames = [set_piece_summary(frame).assign(matchId=match_id) for match_id, frame in self.iter_matches()]
        if not frames:
            return pd.DataFrame()
        detail = pd.concat(frames, ignore_index=True)
        out = detail.groupby(["contestantId", "set_piece_type"], as_index=False).agg(
            matches=("matchId", "nunique"), attempts=("attempts", "sum"),
            successful=("successful", "sum"), shots=("shots", "sum"), goals=("goals", "sum"),
        )
        out["success_rate"] = (out["successful"] / out["attempts"]).round(3)
        out["attempts_per_match"] = (out["attempts"] / out["matches"]).round(2)
        return self._attach_metadata(out)

    def report(self, set_piece_type: str, model=None, retention_window_seconds: float = 8.0) -> pd.DataFrame:
        frames = []
        for match_id, frame in self.iter_matches():
            report = set_piece_report(frame, set_piece_type, model=model, retention_window_seconds=retention_window_seconds)
            frames.append(report.assign(matchId=match_id))
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def rolling_summary(self, window: int = 5) -> pd.DataFrame:
        """Rolling attacking form: attempts/success rate/shots/goals summed
        over the trailing ``window`` matches, per team and set-piece type.

        .. important::
           "Match order" here is simply the order matches first appear in
           ``self.events`` -- i.e. whatever order ``sources``/``match_ids``
           were passed to :meth:`from_sources`. There is no date field in
           the loaded event schema to derive true chronological order
           from, so this is only meaningful if you supplied matches
           already in chronological order (e.g. not a directory listing,
           which sorts alphabetically).
        """
        if window < 1:
            raise ValueError("window must be at least 1")
        frames = [set_piece_summary(frame).assign(matchId=match_id) for match_id, frame in self.iter_matches()]
        if not frames:
            return pd.DataFrame()
        detail = pd.concat(frames, ignore_index=True)
        detail["match_order"] = detail["matchId"].map({mid: i for i, mid in enumerate(self.match_ids)})
        detail = detail.sort_values(["contestantId", "set_piece_type", "match_order"])
        groups = detail.groupby(["contestantId", "set_piece_type"], sort=False)
        for column in ("attempts", "successful", "shots", "goals"):
            detail[f"rolling_{column}"] = groups[column].transform(lambda s: s.rolling(window, min_periods=1).sum())
        detail["rolling_success_rate"] = detail["rolling_successful"] / detail["rolling_attempts"]
        return detail.drop(columns="match_order").reset_index(drop=True)

    def rolling_defensive_summary(self, window: int = 5) -> pd.DataFrame:
        """Rolling defensive form: attempts faced/shots/goals conceded
        summed over the trailing ``window`` matches, per team and
        set-piece type -- the conceding-side mirror of
        :meth:`rolling_summary`, built on
        :func:`~wa_setpieces.core.defending.defensive_set_piece_summary`.

        Same match-order caveat as :meth:`rolling_summary`: only
        meaningful if matches were supplied to :meth:`from_sources`
        already in chronological order.
        """
        if window < 1:
            raise ValueError("window must be at least 1")
        frames = [
            defensive_set_piece_summary(frame).assign(matchId=match_id)
            for match_id, frame in self.iter_matches()
        ]
        if not frames:
            return pd.DataFrame()
        detail = pd.concat(frames, ignore_index=True)
        detail["match_order"] = detail["matchId"].map({mid: i for i, mid in enumerate(self.match_ids)})
        detail = detail.sort_values(["contestantId", "set_piece_type", "match_order"])
        groups = detail.groupby(["contestantId", "set_piece_type"], sort=False)
        for column in ("attempts_faced", "opponent_successful", "shots_conceded", "goals_conceded"):
            detail[f"rolling_{column}"] = groups[column].transform(lambda s: s.rolling(window, min_periods=1).sum())
        detail["rolling_opponent_success_rate"] = (
            detail["rolling_opponent_successful"] / detail["rolling_attempts_faced"]
        ).round(3)
        detail["rolling_shots_conceded_per_100"] = (
            100 * detail["rolling_shots_conceded"] / detail["rolling_attempts_faced"]
        ).round(2)
        return detail.drop(columns="match_order").reset_index(drop=True)

    def _attach_metadata(self, frame: pd.DataFrame) -> pd.DataFrame:
        # Team-level metadata can be attached by contestantId; match-level
        # metadata remains available on ``metadata`` and per-match reports.
        if not self.metadata.empty and "contestantId" in self.metadata:
            team_meta = self.metadata.drop(columns=["matchId"], errors="ignore").drop_duplicates("contestantId")
            return frame.merge(team_meta, on="contestantId", how="left")
        return frame
