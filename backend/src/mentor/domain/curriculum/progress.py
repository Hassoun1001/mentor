"""User-side lesson progress."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class LessonStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class LessonProgress:
    lesson_slug: str
    status: LessonStatus
    last_seen_at: datetime | None
    completed_at: datetime | None
