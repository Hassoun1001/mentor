"""Short names used by the chapter files, so lesson text stays easy to read."""

from __future__ import annotations

from mentor.domain.curriculum.charts import Bar, Chart, HLine, Mark, Path, Segment, Series, Zone
from mentor.domain.curriculum.model import (
    Evidence,
    Figure,
    Lesson,
    Module,
    QuizQuestion,
    Verdict,
)

Q = QuizQuestion

__all__ = [
    "Bar",
    "Chart",
    "Evidence",
    "Figure",
    "HLine",
    "Lesson",
    "Mark",
    "Module",
    "Path",
    "Q",
    "QuizQuestion",
    "Segment",
    "Series",
    "Verdict",
    "Zone",
    "candle_chart",
    "chapter",
    "fact",
]


def chapter(
    part_id: str, chapter_id: str, title: str, summary: str, lessons: tuple[Lesson, ...]
) -> Module:
    """A chapter. The final order and numbering are assigned by the catalog."""
    return Module(
        id=chapter_id, order=0, title=title, summary=summary, lessons=lessons, part_id=part_id
    )


def fact(text_md: str) -> Evidence:
    """The evidence box for a lesson that defines something rather than claims something."""
    return Evidence(Verdict.FACT, text_md)


def candle_chart(
    p: Path,
    *,
    title: str,
    caption: str,
    place: str = "explain",
    series: tuple[Series, ...] = (),
    hlines: tuple[HLine, ...] = (),
    zones: tuple[Zone, ...] = (),
    marks: tuple[Mark, ...] = (),
    segments: tuple[Segment, ...] = (),
    lower_title: str = "",
) -> Chart:
    """A candlestick chart of made-up prices. It is always labelled illustrative."""
    return Chart(
        title=title,
        caption=caption,
        data_kind="illustrative",
        kind="candles",
        place="example" if place == "example" else "explain",
        candles=p.candles,
        series=series,
        hlines=hlines,
        zones=zones,
        marks=marks,
        segments=segments,
        lower_title=lower_title,
    )
