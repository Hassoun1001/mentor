"""Every entry point must import on its own, in a fresh interpreter.

In-process tests can't catch an import cycle: by the time one runs, some
earlier test has usually imported the modules in a working order. The
health layer once imported the scheduler package, which imported the health
layer back — the app booted fine, but anything that loaded the self-report
first crashed. Each module here is imported alone, in its own process.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_ENTRY_POINTS = (
    "mentor.application.health.self_report",
    "mentor.application.health.collect",
    "mentor.application.alerts.messages",
    "mentor.application.scheduler.quality_gate",
    "mentor.application.scheduler.service",
    "mentor.main",
)


@pytest.mark.parametrize("module", _ENTRY_POINTS)
def test_module_imports_first_in_a_fresh_process(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
