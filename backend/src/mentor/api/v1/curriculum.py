"""Curriculum endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mentor.api.deps import SessionDep
from mentor.application.curriculum import CurriculumService
from mentor.application.curriculum.service import LessonWithProgress
from mentor.domain.curriculum import GLOSSARY, SOURCES, list_parts, search_lessons
from mentor.domain.curriculum.charts import Chart
from mentor.domain.curriculum.progress import LessonStatus
from mentor.domain.errors import ValidationError
from mentor.infrastructure.repositories import LessonProgressRepository

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


class LessonSummary(BaseModel):
    slug: str
    title: str
    summary: str
    est_minutes: int
    order_in_module: int
    key_concepts: list[str]
    status: LessonStatus
    last_seen_at: datetime | None


class ModuleSummary(BaseModel):
    id: str
    order: int
    part_id: str
    title: str
    summary: str
    est_minutes: int
    completed_count: int
    total_count: int
    is_complete: bool
    lessons: list[LessonSummary]


class PartDTO(BaseModel):
    id: str
    order: int
    stage: str
    title: str
    summary: str


class FigureDTO(BaseModel):
    key: str
    caption: str


class QuizQuestionDTO(BaseModel):
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str


class EvidenceDTO(BaseModel):
    verdict: str
    text_md: str


class LessonResponse(BaseModel):
    slug: str
    module_id: str
    order_in_module: int
    title: str
    summary: str
    body_md: str
    est_minutes: int
    key_concepts: list[str]
    figures: list[FigureDTO]
    quiz: list[QuizQuestionDTO]
    status: LessonStatus
    goal: str
    charts: list[Chart]
    steps: list[str]
    example_md: str
    mistakes: list[str]
    evidence: EvidenceDTO | None
    try_it: str
    takeaways: list[str]
    sources: list[str]


class MarkRequest(BaseModel):
    status: LessonStatus


class SearchHitDTO(BaseModel):
    slug: str
    title: str
    summary: str
    snippet: str


class GlossaryTermDTO(BaseModel):
    term: str
    definition: str


class SourceDTO(BaseModel):
    key: str
    authors: str
    year: str
    title: str
    url: str
    note: str
    topic: str
    checked: bool


def _service(session: SessionDep) -> CurriculumService:
    return CurriculumService(LessonProgressRepository(session))


@router.get("/overview", response_model=list[ModuleSummary])
async def overview(session: SessionDep) -> list[ModuleSummary]:
    modules = await _service(session).overview()
    return [
        ModuleSummary(
            id=m.module.id,
            order=m.module.order,
            part_id=m.module.part_id,
            title=m.module.title,
            summary=m.module.summary,
            est_minutes=m.module.est_minutes,
            completed_count=m.completed_count,
            total_count=m.total_count,
            is_complete=m.is_complete,
            lessons=[
                LessonSummary(
                    slug=lp.lesson.slug,
                    title=lp.lesson.title,
                    summary=lp.lesson.summary,
                    est_minutes=lp.lesson.est_minutes,
                    order_in_module=lp.lesson.order_in_module,
                    key_concepts=list(lp.lesson.key_concepts),
                    status=lp.progress.status if lp.progress else LessonStatus.NOT_STARTED,
                    last_seen_at=lp.progress.last_seen_at if lp.progress else None,
                )
                for lp in m.lessons
            ],
        )
        for m in modules
    ]


@router.get("/parts", response_model=list[PartDTO])
async def parts() -> list[PartDTO]:
    return [
        PartDTO(id=p.id, order=p.order, stage=p.stage, title=p.title, summary=p.summary)
        for p in list_parts()
    ]


@router.get("/search", response_model=list[SearchHitDTO])
async def search(q: str = Query(min_length=2, max_length=80)) -> list[SearchHitDTO]:
    return [
        SearchHitDTO(
            slug=hit.lesson.slug,
            title=hit.lesson.title,
            summary=hit.lesson.summary,
            snippet=hit.snippet,
        )
        for hit in search_lessons(q)
    ]


@router.get("/glossary", response_model=list[GlossaryTermDTO])
async def glossary() -> list[GlossaryTermDTO]:
    return [GlossaryTermDTO(term=t.term, definition=t.definition) for t in GLOSSARY]


@router.get("/sources", response_model=list[SourceDTO])
async def sources() -> list[SourceDTO]:
    return [
        SourceDTO(
            key=s.key,
            authors=s.authors,
            year=s.year,
            title=s.title,
            url=s.url,
            note=s.note,
            topic=s.topic,
            checked=s.checked,
        )
        for s in SOURCES
    ]


@router.get("/parts/{part_id}/lessons", response_model=list[LessonResponse])
async def part_lessons(part_id: str, session: SessionDep) -> list[LessonResponse]:
    return [_lesson_response(lp) for lp in await _service(session).lessons_in_part(part_id)]


@router.get("/lessons/{slug:path}", response_model=LessonResponse)
async def get_lesson(slug: str, session: SessionDep) -> LessonResponse:
    try:
        lp = await _service(session).get(slug)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _lesson_response(lp)


def _lesson_response(lp: LessonWithProgress) -> LessonResponse:
    lesson = lp.lesson
    return LessonResponse(
        slug=lesson.slug,
        module_id=lesson.module_id,
        order_in_module=lesson.order_in_module,
        title=lesson.title,
        summary=lesson.summary,
        body_md=lesson.body_md,
        est_minutes=lesson.est_minutes,
        key_concepts=list(lesson.key_concepts),
        figures=[FigureDTO(key=f.key, caption=f.caption) for f in lesson.figures],
        quiz=[
            QuizQuestionDTO(
                prompt=q.prompt,
                options=list(q.options),
                correct_index=q.correct_index,
                explanation=q.explanation,
            )
            for q in lesson.quiz
        ],
        status=lp.progress.status if lp.progress else LessonStatus.NOT_STARTED,
        goal=lesson.goal,
        charts=list(lesson.charts),
        steps=list(lesson.steps),
        example_md=lesson.example_md,
        mistakes=list(lesson.mistakes),
        evidence=(
            EvidenceDTO(verdict=lesson.evidence.verdict.value, text_md=lesson.evidence.text_md)
            if lesson.evidence
            else None
        ),
        try_it=lesson.try_it,
        takeaways=list(lesson.takeaways),
        sources=list(lesson.sources),
    )


@router.post("/lessons/{slug:path}/progress", response_model=LessonResponse)
async def mark_progress(slug: str, body: MarkRequest, session: SessionDep) -> LessonResponse:
    service = _service(session)
    try:
        await service.mark(slug, body.status)
        lp = await service.get(slug)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _lesson_response(lp)
