"""Curriculum endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mentor.api.deps import SessionDep
from mentor.application.curriculum import CurriculumService
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


class ModuleSummary(BaseModel):
    id: str
    order: int
    title: str
    summary: str
    est_minutes: int
    completed_count: int
    total_count: int
    is_complete: bool
    lessons: list[LessonSummary]


class LessonResponse(BaseModel):
    slug: str
    module_id: str
    order_in_module: int
    title: str
    summary: str
    body_md: str
    est_minutes: int
    key_concepts: list[str]
    status: LessonStatus


class MarkRequest(BaseModel):
    status: LessonStatus


def _service(session: SessionDep) -> CurriculumService:
    return CurriculumService(LessonProgressRepository(session))


@router.get("/overview", response_model=list[ModuleSummary])
async def overview(session: SessionDep) -> list[ModuleSummary]:
    modules = await _service(session).overview()
    return [
        ModuleSummary(
            id=m.module.id,
            order=m.module.order,
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
                )
                for lp in m.lessons
            ],
        )
        for m in modules
    ]


@router.get("/lessons/{slug:path}", response_model=LessonResponse)
async def get_lesson(slug: str, session: SessionDep) -> LessonResponse:
    try:
        lp = await _service(session).get(slug)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LessonResponse(
        slug=lp.lesson.slug,
        module_id=lp.lesson.module_id,
        order_in_module=lp.lesson.order_in_module,
        title=lp.lesson.title,
        summary=lp.lesson.summary,
        body_md=lp.lesson.body_md,
        est_minutes=lp.lesson.est_minutes,
        key_concepts=list(lp.lesson.key_concepts),
        status=lp.progress.status if lp.progress else LessonStatus.NOT_STARTED,
    )


@router.post("/lessons/{slug:path}/progress", response_model=LessonResponse)
async def mark_progress(slug: str, body: MarkRequest, session: SessionDep) -> LessonResponse:
    service = _service(session)
    try:
        await service.mark(slug, body.status)
        lp = await service.get(slug)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LessonResponse(
        slug=lp.lesson.slug,
        module_id=lp.lesson.module_id,
        order_in_module=lp.lesson.order_in_module,
        title=lp.lesson.title,
        summary=lp.lesson.summary,
        body_md=lp.lesson.body_md,
        est_minutes=lp.lesson.est_minutes,
        key_concepts=list(lp.lesson.key_concepts),
        status=lp.progress.status if lp.progress else LessonStatus.NOT_STARTED,
    )
