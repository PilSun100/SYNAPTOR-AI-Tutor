from sqlalchemy.orm import Session

from app.models.learning import Concept, ConceptMastery, LearningSession, MaterialMastery, UserAnswer, utc_now
from app.services.concept_normalization_service import canonical_concepts

TIERS = [
    (40, "초심자"),
    (60, "견습생"),
    (75, "숙련자"),
    (90, "탐구자"),
    (101, "현자"),
]

HINT_BUDGET_BY_DIFFICULTY = {
    "easy": 3,
    "medium": 4,
    "hard": 5,
}


def hint_budget_for_difficulty(difficulty: str | None) -> int:
    return HINT_BUDGET_BY_DIFFICULTY.get((difficulty or "").lower(), 4)


def tier_for_score(score: float) -> str:
    normalized = max(0.0, min(100.0, score))
    for threshold, tier in TIERS:
        if normalized < threshold:
            return tier
    return "현자"


def concept_score(answer: UserAnswer, hints_used: int) -> float:
    hint_budget = hint_budget_for_difficulty(answer.question.concept.difficulty)
    hint_efficiency = max(0.0, 1.0 - (hints_used / max(hint_budget, 1)))
    score = (answer.correctness_score * 65) + (hint_efficiency * 25) + 10
    return round(max(0.0, min(100.0, score)), 1)


def apply_concept_score(mastery: ConceptMastery, score: float) -> ConceptMastery:
    mastery.concept_score = score
    mastery.tier_name = tier_for_score(score)
    return mastery


def update_material_mastery(db: Session, session: LearningSession) -> MaterialMastery | None:
    if session.user_id is None:
        return None

    concepts = (
        db.query(Concept)
        .filter(Concept.material_id == session.material_id)
        .order_by(Concept.id.asc())
        .all()
    )
    concepts = canonical_concepts(concepts)
    total_concepts = len(concepts)
    if total_concepts == 0:
        return None

    concept_ids = [concept.id for concept in concepts]
    answered_concept_ids = {
        answer.question.concept_id
        for answer in (
            db.query(UserAnswer)
            .join(LearningSession, UserAnswer.session_id == LearningSession.id)
            .filter(
                LearningSession.user_id == session.user_id,
                LearningSession.material_id == session.material_id,
            )
            .all()
        )
        if answer.question.concept_id in concept_ids
    }

    completed_concepts = len(answered_concept_ids)
    completed_scores = [
        concept.mastery.concept_score
        for concept in concepts
        if concept.id in answered_concept_ids and concept.mastery is not None
    ]
    material_score = round(sum(completed_scores) / len(completed_scores), 1) if completed_scores else 0.0

    material_mastery = (
        db.query(MaterialMastery)
        .filter(
            MaterialMastery.user_id == session.user_id,
            MaterialMastery.material_id == session.material_id,
        )
        .one_or_none()
    )
    if material_mastery is None:
        material_mastery = MaterialMastery(
            user_id=session.user_id,
            material_id=session.material_id,
        )
        db.add(material_mastery)
        db.flush()

    material_mastery.material_score = material_score
    material_mastery.tier_name = tier_for_score(material_score)
    material_mastery.completed_concepts = completed_concepts
    material_mastery.total_concepts = total_concepts
    material_mastery.updated_at = utc_now()
    return material_mastery
