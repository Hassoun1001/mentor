"""Live recalibration plumbing — which calls are the champion's, and where
the correction lives between retrains.

The fitting itself is pure (`domain/forecasting/live_recalibration.py`).
This module answers the two questions around it that need the outside
world:

- **Whose calls are these?** The predictions table records the forecaster's
  *kind* (``regime_adjusted(sklearn_hgb(h=24,macro))``), not which trained
  model made the call, and baseline-rule calls are interleaved on the same
  lane whenever something asks for them. A champion's live record is
  therefore every non-baseline live call on its lane made at or after it
  took the crown — the only model that could have produced them.
- **What is in force right now?** The latest decision is written next to
  the champion pointer as ``live_calibration.json``. Inference applies it
  only when it was applied *and* names the model being asked for, so a
  newly promoted champion starts on its own calibration automatically.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from mentor.domain.forecasting.live_recalibration import LiveRecalibration
from mentor.domain.stats.independence import select_independent
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.live_calibration")

_LIVE_CALIBRATION_FILE = "live_calibration.json"


class _ResolvedCall(Protocol):
    """The slice of a prediction row the attribution needs."""

    @property
    def asof(self) -> datetime: ...
    @property
    def horizon_at(self) -> datetime: ...
    @property
    def model_name(self) -> str: ...
    @property
    def p_up(self) -> object: ...
    @property
    def p_up_model(self) -> object: ...
    @property
    def realised_outcome(self) -> int | None: ...


def champion_live_calls(
    rows: Sequence[_ResolvedCall], *, promoted_at: datetime
) -> list[tuple[float, int]]:
    """The champion's independent resolved live calls, oldest first.

    ``rows`` should already be one lane's resolved live predictions; this
    keeps only what the champion can have said (non-baseline, at or after
    promotion), reads the model's own probability rather than any corrected
    one, and collapses overlapping outcome windows to independent ones.
    """
    calls: list[tuple[datetime, datetime, float, int]] = []
    for r in rows:
        if r.realised_outcome is None or r.asof < promoted_at:
            continue
        if r.model_name.startswith("baseline"):
            continue  # the rule model shares the lane; its calls are not the champion's
        own = r.p_up_model if r.p_up_model is not None else r.p_up
        calls.append((r.asof, r.horizon_at, float(str(own)), int(r.realised_outcome)))
    # select_independent walks newest-first; the fit wants time order.
    return list(reversed(select_independent(calls)))


def parse_promoted_at(champion: dict[str, object] | None) -> datetime | None:
    """The champion's promotion time, or None if it is missing or malformed."""
    raw = (champion or {}).get("promoted_at")
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


class LiveCalibrationStore:
    """The correction currently in force for a lane's champion."""

    def __init__(self, model_store_dir: str | Path) -> None:
        self._path = Path(model_store_dir) / _LIVE_CALIBRATION_FILE

    def read(self) -> dict[str, object] | None:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # A torn or unreadable file must degrade to "no correction",
            # never to a failed forecast.
            log.warning("live_calibration.unreadable", path=str(self._path))
            return None
        return data if isinstance(data, dict) else None

    def write(
        self, *, model_name: str, decided_at: datetime, result: LiveRecalibration
    ) -> dict[str, object]:
        entry: dict[str, object] = {
            "model_name": model_name,
            "decided_at": decided_at.isoformat(),
            **result.to_dict(),
        }
        # Write-then-rename so a forecast running mid-retrain never reads a
        # half-written file.
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)
        return entry

    def clear(self) -> None:
        self._path.unlink(missing_ok=True)

    def active_slope_for(self, model_name: str) -> float:
        """The slope to apply to ``model_name``'s forecasts; 1.0 = none.

        Only a decision that was applied, for exactly this model, counts —
        a correction learned from one champion says nothing about the next.
        """
        data = self.read()
        if not data or data.get("model_name") != model_name or data.get("applied") is not True:
            return 1.0
        slope = data.get("slope")
        if not isinstance(slope, (int, float)) or isinstance(slope, bool) or slope < 0:
            return 1.0
        return float(slope)
