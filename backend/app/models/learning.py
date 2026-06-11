from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.vector import EmbeddingVector


def utc_now() -> datetime:
    return datetime.now(UTC)


class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User | None"] = relationship(back_populates="materials")
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["MaterialChunk"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )


class MaterialChunk(Base):
    __tablename__ = "material_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("learning_materials.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    material: Mapped[LearningMaterial] = relationship(back_populates="chunks")
    evidence_logs: Mapped[list["EvidenceLog"]] = relationship(
        back_populates="chunk",
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
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("learning_materials.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="sessions")
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
    user_answer_id: Mapped[int | None] = mapped_column(ForeignKey("user_answers.id"), nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("learning_sessions.id"), nullable=True)
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"), nullable=True)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    hint_level: Mapped[int] = mapped_column(Integer, nullable=False)
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    stuck_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user_answer: Mapped[UserAnswer | None] = relationship(back_populates="hints")


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("material_chunks.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)
    related_question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"), nullable=True)
    related_answer_id: Mapped[int | None] = mapped_column(ForeignKey("user_answers.id"), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    chunk: Mapped[MaterialChunk] = relationship(back_populates="evidence_logs")


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
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False, unique=True)
    mastery_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cognitive_load_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    last_answer_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    misconception_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hint_dependency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_speed_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    next_difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="diagnostic")
    next_question_type: Mapped[str] = mapped_column(String(100), nullable=False, default="definition")
    learner_level_label: Mapped[str] = mapped_column(String(100), nullable=False, default="진단 전")
    recommended_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personalized_explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hint_used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    concept_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tier_name: Mapped[str] = mapped_column(String(50), nullable=False, default="초심자")

    user: Mapped["User | None"] = relationship(back_populates="mastery_records")
    concept: Mapped[Concept] = relationship(back_populates="mastery")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    materials: Mapped[list[LearningMaterial]] = relationship(back_populates="user")
    sessions: Mapped[list[LearningSession]] = relationship(back_populates="user")
    mastery_records: Mapped[list[ConceptMastery]] = relationship(back_populates="user")
    learning_profile: Mapped["UserLearningProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    material_mastery_records: Mapped[list["MaterialMastery"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class UserLearningProfile(Base):
    __tablename__ = "user_learning_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    average_recall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    explanation_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hint_dependency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    misconception_frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    preferred_difficulty_level: Mapped[str] = mapped_column(String(50), nullable=False, default="easy")
    frustration_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    best_intervention_type: Mapped[str] = mapped_column(String(100), nullable=False, default="active_recall")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped[User] = relationship(back_populates="learning_profile")


class MaterialMastery(Base):
    __tablename__ = "material_mastery"
    __table_args__ = (UniqueConstraint("user_id", "material_id", name="uq_material_mastery_user_material"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("learning_materials.id"), nullable=False)
    material_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tier_name: Mapped[str] = mapped_column(String(50), nullable=False, default="초심자")
    completed_concepts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_concepts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped[User] = relationship(back_populates="material_mastery_records")
    material: Mapped[LearningMaterial] = relationship()
