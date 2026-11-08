"""Writes the Learn docs from the catalog: table of contents, lesson map, sources.

Usage (from backend/): python scripts/generate_learn_docs.py
"""

from __future__ import annotations

from pathlib import Path

from mentor.domain.curriculum import ATLAS, CATALOG, SOURCES, USAGE_NOTE, list_parts
from mentor.domain.curriculum.book.first_edition import FIRST_EDITION_SLUGS

DOCS = Path(__file__).resolve().parents[2] / "docs" / "learn"


def _table_of_contents() -> str:
    lines = ["# The trading book - table of contents", ""]
    for part in list_parts():
        lines += [f"## {part.stage}: {part.title}", "", part.summary, ""]
        for module in (m for m in CATALOG if m.part_id == part.id):
            lines += [f"### {module.title}", ""]
            lines += [f"- {lesson.title} (`{lesson.slug}`)" for lesson in module.lessons]
            lines += [""]
    return "\n".join(lines)


def _lesson_map() -> str:
    parts = {part.id: part for part in list_parts()}
    lines = [
        "# First edition to book mapping",
        "",
        "Every lesson slug is permanent, and reading progress is keyed by slug.",
        "The first-edition lessons below keep their slug, so progress carries over.",
        "",
        "| Slug | Edition | Stage | Chapter |",
        "|---|---|---|---|",
    ]
    first = set(FIRST_EDITION_SLUGS)
    for module in CATALOG:
        part = parts[module.part_id]
        for lesson in module.lessons:
            edition = "first edition, rewritten" if lesson.slug in first else "new"
            lines.append(
                f"| {lesson.slug} | {edition} | {part.stage}: {part.title} | {module.title} |"
            )
    return "\n".join(lines) + "\n"


def _sources() -> str:
    lines = [
        "# Sources for the trading book",
        "",
        "Claims are written in the book's own words. 'Not re-opened' marks a source",
        "cited from general knowledge rather than checked during the research pass.",
        "",
    ]
    topics = sorted({source.topic for source in SOURCES})
    for topic in topics:
        lines += [f"## {topic}", ""]
        for source in (s for s in SOURCES if s.topic == topic):
            tag = "" if source.checked else " (not re-opened)"
            cite = f"{source.authors} ({source.year}). [{source.title}]({source.url}){tag}"
            lines.append(f"- {cite}: {source.note}")
        lines += [""]
    return "\n".join(lines)


def _atlas() -> str:
    lines = ["# Methods Atlas", "", USAGE_NOTE, ""]
    for group in ATLAS:
        lines += [f"## {group.letter}. {group.title}", "", group.summary, ""]
        lines += ["| Method | Usage label | Evidence label | Full lesson |", "|---|---|---|---|"]
        for m in group.methods:
            lesson = f"`{m.lesson}`" if m.lesson else "card only"
            lines.append(f"| {m.name} | {m.usage.value} | {m.verdict.value} | {lesson} |")
        lines += [""]
    return "\n".join(lines)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "TABLE_OF_CONTENTS.md").write_text(_table_of_contents(), encoding="utf-8")
    (DOCS / "LESSON_MAP.md").write_text(_lesson_map(), encoding="utf-8")
    (DOCS / "SOURCES.md").write_text(_sources(), encoding="utf-8")
    (DOCS / "METHODS_ATLAS.md").write_text(_atlas(), encoding="utf-8")


if __name__ == "__main__":
    main()
