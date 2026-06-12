from sqlalchemy.orm import Session

from app.models.learning import LearningMaterial
from app.services.llm_provider import GeneratedTutorChat, LLMProvider
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
    if not evidence_chunks:
        reply = _no_evidence_reply(message)
        return (
            reply.reply,
            reply.learning_mode,
            reply.next_action,
            reply.suggested_questions,
            evidence_chunks,
        )

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


def _no_evidence_reply(message: str) -> GeneratedTutorChat:
    return GeneratedTutorChat(
        reply=(
            "업로드된 자료에서 이 질문을 뒷받침할 근거를 찾지 못했습니다. "
            "자료에 나온 개념명이나 슬라이드의 핵심 키워드로 다시 질문해보세요."
        ),
        learning_mode="evidence_check",
        next_action="Study에서 자료가 올바르게 업로드됐는지 확인한 뒤, 자료 안의 용어로 다시 질문해보세요.",
        suggested_questions=[
            "이 자료에서 중요한 개념을 짧게 정리해줘",
            "자료에 나온 키워드 기준으로 다시 설명해줘",
            f"'{message[:40]}'와 관련된 자료 근거가 있는지 확인해줘",
        ],
    )
