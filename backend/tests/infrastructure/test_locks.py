"""The retrain lock: one holder at a time, released on exit."""

from __future__ import annotations

from pathlib import Path

from mentor.infrastructure.locks import try_exclusive


def test_a_second_holder_stands_aside_until_the_first_lets_go(tmp_path: Path) -> None:
    lock = tmp_path / "store" / ".retrain.lock"
    with try_exclusive(lock) as first:
        assert first
        with try_exclusive(lock) as second:
            assert not second
    with try_exclusive(lock) as again:
        assert again


def test_separate_lanes_do_not_block_each_other(tmp_path: Path) -> None:
    with (
        try_exclusive(tmp_path / ".retrain.lock") as h1,
        try_exclusive(tmp_path / "d1" / ".retrain.lock") as d1,
    ):
        assert h1 and d1
