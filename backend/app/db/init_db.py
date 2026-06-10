from pathlib import Path

from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import learning


def init_db() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    if not settings.auto_create_tables:
        return

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_adaptive_columns()
    _ensure_sqlite_auth_columns()
    _ensure_sqlite_embedding_columns()


def _ensure_sqlite_adaptive_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "concept_mastery" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("concept_mastery")}
    adaptive_columns = {
        "confidence_score": "FLOAT NOT NULL DEFAULT 0.0",
        "cognitive_load_score": "FLOAT NOT NULL DEFAULT 0.5",
        "last_answer_quality": "FLOAT NOT NULL DEFAULT 0.0",
        "misconception_count": "INTEGER NOT NULL DEFAULT 0",
        "hint_dependency": "FLOAT NOT NULL DEFAULT 0.0",
        "response_speed_score": "FLOAT NOT NULL DEFAULT 0.5",
        "next_difficulty": "VARCHAR(50) NOT NULL DEFAULT 'diagnostic'",
        "next_question_type": "VARCHAR(100) NOT NULL DEFAULT 'definition'",
        "learner_level_label": "VARCHAR(100) NOT NULL DEFAULT '진단 전'",
        "recommended_strategy": "TEXT NOT NULL DEFAULT ''",
        "personalized_explanation": "TEXT NOT NULL DEFAULT ''",
    }

    with engine.begin() as connection:
        for column_name, definition in adaptive_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE concept_mastery ADD COLUMN {column_name} {definition}")
                )


def _ensure_sqlite_auth_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_columns = {
        table_name: {column["name"] for column in inspector.get_columns(table_name)}
        for table_name in inspector.get_table_names()
    }
    auth_columns = {
        "learning_materials": {"user_id": "INTEGER"},
        "learning_sessions": {"user_id": "INTEGER"},
        "concept_mastery": {"user_id": "INTEGER"},
    }

    with engine.begin() as connection:
        for table_name, columns in auth_columns.items():
            if table_name not in table_columns:
                continue
            for column_name, definition in columns.items():
                if column_name not in table_columns[table_name]:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
                    )


def _ensure_sqlite_embedding_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "material_chunks" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("material_chunks")}
    embedding_columns = {
        "chunk_type": "VARCHAR(50) NOT NULL DEFAULT 'text'",
        "embedding": "TEXT",
        "embedding_model": "VARCHAR(100)",
    }

    with engine.begin() as connection:
        for column_name, definition in embedding_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE material_chunks ADD COLUMN {column_name} {definition}")
                )
