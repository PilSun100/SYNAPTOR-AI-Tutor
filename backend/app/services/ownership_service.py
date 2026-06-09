from fastapi import HTTPException, status

from app.models.learning import Concept, LearningMaterial, LearningSession, Question, User, UserAnswer


def ensure_material_owner(material: LearningMaterial, user: User) -> None:
    if material.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 자료를 찾을 수 없습니다.",
        )


def ensure_concept_owner(concept: Concept, user: User) -> None:
    ensure_material_owner(concept.material, user)


def ensure_question_owner(question: Question, user: User) -> None:
    ensure_concept_owner(question.concept, user)


def ensure_session_owner(session: LearningSession, user: User) -> None:
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 세션을 찾을 수 없습니다.",
        )


def ensure_answer_owner(answer: UserAnswer, user: User) -> None:
    ensure_session_owner(answer.session, user)
