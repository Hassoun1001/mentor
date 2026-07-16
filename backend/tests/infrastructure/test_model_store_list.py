"""ModelStore.list() must ignore non-model sidecars (regression).

champion.json lives in the model store dir but is not model metadata (it
has no 'report' key). The listing globbed *.json and crashed on it with
KeyError: 'report', 500-ing GET /forecasting/models. list() must skip any
JSON without a matching .joblib artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

from mentor.infrastructure.forecasting.model_store import ModelStore


def test_list_skips_champion_and_malformed_sidecars(tmp_path: Path) -> None:
    store = ModelStore(tmp_path)

    # A champion pointer — real shape, no matching .joblib, no 'report'.
    (tmp_path / "champion.json").write_text(
        json.dumps({"model_name": "x", "test_brier": 0.24, "promoted_at": "2026-01-01T00:00:00Z"}),
        encoding="utf-8",
    )
    # A JSON with a matching artifact but corrupt contents.
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "broken.joblib").write_bytes(b"stub")

    # No crash, and neither sidecar is surfaced as a model.
    assert list(store.list()) == []
