from sqlalchemy.orm import Session

from app.models.learning import Concept, Question
from app.services.llm_provider import LLMProvider
from app.services.retrieval_service import format_evidence_context, log_evidence, retrieve_chunks_for_concept


def generate_and_store_questions(
    db: Session,
    concept: Concept,
    provider: LLMProvider,
) -> tuple[str, list[Question]]:
    material_text = concept.material.extracted_text if concept.material else ""
    evidence_chunks = retrieve_chunks_for_concept(db, concept.id)
    generated = provider.generate_questions(
        concept_title=concept.title,
        concept_description=concept.description,
        material_text=material_text,
        evidence_context=format_evidence_context(evidence_chunks),
    )

    questions = [
        Question(
            concept_id=concept.id,
            question_text=item.question_text,
            question_type=item.question_type,
            expected_answer=item.expected_answer,
        )
        for item in generated
    ]

    db.add_all(questions)
    db.flush()
    for question in questions:
        log_evidence(
            db,
            evidence_chunks,
            purpose="question_generation",
            related_question_id=question.id,
        )
    db.commit()

    for question in questions:
        db.refresh(question)

    return provider.source, questions
