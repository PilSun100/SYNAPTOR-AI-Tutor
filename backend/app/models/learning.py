from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("learning_materials.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    parent_concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    material: Mapped[LearningMaterial] = relationship(back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
    )
    mastery: Mapped["ConceptMastery | None"] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    concept: Mapped[Concept] = relationship(back_populates="questions")
    answers: Mapped[list["UserAnswer"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("learning_materials.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    material: Mapped[LearningMaterial] = relationship(back_populates="sessions")
    answers: Mapped[list["UserAnswer"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("learning_sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    correctness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    missing_points: Mapped[str] = mapped_column(Text, nullable=False, default="")
    misconception_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    response_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    session: Mapped[LearningSession] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="answers")
    hints: Mapped[list["HintLog"]] = relationship(
        back_populates="user_answer",
        cascade="all, delete-orphan",
    )


class HintLog(Base):
    __tablename__ = "hint_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_answer_id: Mapped[int] = mapped_column(ForeignKey("user_answers.id"), nullable=False)
    hint_level: Mapped[int] = mapped_column(Integer, nullable=False)
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user_answer: Mapped[UserAnswer] = relationship(back_populates="hints")


class SelfExplanation(Base):
    __tablename__ = "self_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    logical_connection_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False, unique=True)
    mastery_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hint_used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    concept: Mapped[Concept] = relationship(back_populates="mastery")
