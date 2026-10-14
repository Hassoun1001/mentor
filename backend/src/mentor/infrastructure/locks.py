"""A non-blocking lock shared by every process that sees the same file.

Retraining writes the model store (challenger files, champion pointer,
promotions log, live calibration). The scheduler retrains on its weekly
slot and on drift; an operator can also retrain from the command line in
the same container. Two retrains of one lane at once would race on those
files, so each takes this lock and the second one stands aside. The OS
releases it if the holder dies, so a crash never leaves it stuck.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

if sys.platform == "win32":  # local development only; production is Linux
    import msvcrt

    def _lock(fd: int) -> None:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def _unlock(fd: int) -> None:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def try_exclusive(path: Path) -> Iterator[bool]:
    """Hold an exclusive lock on ``path`` if it is free; yield whether it was."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            _lock(fd)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            _unlock(fd)
    finally:
        os.close(fd)
