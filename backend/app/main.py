from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.answers import router as answers_router
from app.api.concepts import router as concepts_router
from app.api.health import router as health_router
from app.api.hints import router as hints_router
from app.api.materials import router as materials_router
from app.api.questions import router as questions_router
from app.api.reports import router as reports_router
from app.api.self_explanations import router as self_explanations_router
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for the Brain-Sync AI Tutor MVP.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(answers_router, prefix="/api", tags=["answers"])
    app.include_router(concepts_router, prefix="/api", tags=["concepts"])
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(hints_router, prefix="/api", tags=["hints"])
    app.include_router(materials_router, prefix="/api", tags=["materials"])
    app.include_router(questions_router, prefix="/api", tags=["questions"])
    app.include_router(reports_router, prefix="/api", tags=["reports"])
    app.include_router(
        self_explanations_router,
        prefix="/api",
        tags=["self-explanations"],
    )

    return app


app = create_app()
