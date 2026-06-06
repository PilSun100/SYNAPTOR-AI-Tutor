from sqlalchemy.orm import Session

from app.models.learning import Concept, ConceptMastery, SelfExplanation
from app.services.adaptive_learning_service import update_mastery_from_self_explanation
from app.services.llm_provider import LLMProvider


def evaluate_and_store_self_explanation(
    db: Session,
    concept: Concept,
    explanation_text: str,
    provider: LLMProvider,
) -> tuple[str, SelfExplanation, ConceptMastery, str]:
    evaluation = provider.evaluate_self_explanation(
        concept_title=concept.title,
        concept_description=concept.description,
        explanation_text=explanation_text,
    )

    self_explanation = SelfExplanation(
        concept_id=concept.id,
        explanation_text=explanation_text,
        accuracy_score=evaluation.accuracy_score,
        completeness_score=evaluation.completeness_score,
        logical_connection_score=evaluation.logical_connection_score,
    )
    db.add(self_explanation)
    db.flush()

    mastery = update_mastery_from_self_explanation(
        db=db,
        concept=concept,
        score=(
            evaluation.accuracy_score
            + evaluation.completeness_score
            + evaluation.logical_connection_score
        )
        / 3,
    )
    db.commit()
    db.refresh(self_explanation)
    db.refresh(mastery)

    return provider.source, self_explanation, mastery, evaluation.feedback
