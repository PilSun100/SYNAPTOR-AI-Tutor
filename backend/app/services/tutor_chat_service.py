from sqlalchemy.orm import Session

from app.models.learning import LearningMaterial
from app.services.llm_provider import LLMProvider
from app.services.retrieval_service import (
    RetrievedChunk,
    format_evidence_context,
    log_evidence,
    retrieve_chunks_by_query,
)


def generate_material_chat_reply(
    db: Session,
    material: LearningMaterial,
    message: str,
    provider: LLMProvider,
) -> tuple[str, str, str, list[str], list[RetrievedChunk]]:
    evidence_chunks = retrieve_chunks_by_query(db, material.id, message, top_k=6)
    evidence_context = format_evidence_context(evidence_chunks)
    reply = provider.generate_tutor_chat(message, evidence_context)

    log_evidence(
        db,
        evidence_chunks,
        purpose="tutor_chat",
    )
    db.commit()

    return (
        reply.reply,
        reply.learning_mode,
        reply.next_action,
        reply.suggested_questions,
        evidence_chunks,
    )
