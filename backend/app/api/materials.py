from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import (
    Concept,
    EvidenceLog,
    HintLog,
    LearningMaterial,
    LearningSession,
    MaterialMastery,
    Question,
    SelfExplanation,
    User,
    UserAnswer,
)
from app.schemas.materials import MaterialListResponse, MaterialSummaryResponse, MaterialUploadResponse
from app.schemas.study import MaterialMasterySummary, StudyConceptItem, StudyStartResponse
from app.services.concept_service import extract_and_store_concepts
from app.services.concept_normalization_service import base_concept_title, canonical_concepts
from app.services.embedding_service import embed_material_chunks
from app.services.llm_provider import get_llm_provider
from app.services.material_chunk_service import build_material_chunks
from app.services.ownership_service import ensure_material_owner
from app.services.pdf_service import extract_pdf_pages, join_page_texts, save_upload_file, validate_pdf_upload
from app.services.question_service import generate_and_store_questions
from app.services.tier_service import hint_budget_for_difficulty, update_material_mastery
from app.services.visual_chunk_service import build_visual_description_chunks

router = APIRouter()


@router.get("/materials", response_model=MaterialListResponse)
def list_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialListResponse:
    materials = (
        db.query(LearningMaterial)
        .filter(LearningMaterial.user_id == current_user.id)
        .order_by(LearningMaterial.created_at.desc())
        .all()
    )

    return MaterialListResponse(
        materials=[
            MaterialSummaryResponse(
                id=material.id,
                title=material.title,
                extracted_text_length=len(material.extracted_text),
                preview=material.extracted_text[:220],
                created_at=material.created_at,
            )
            for material in materials
        ]
    )


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    material = db.get(LearningMaterial, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 자료를 찾을 수 없습니다.",
        )
    ensure_material_owner(material, current_user)

    concept_ids = [concept.id for concept in material.concepts]
    question_ids = [
        question.id
        for concept in material.concepts
        for question in concept.questions
    ]
    session_ids = [session.id for session in material.sessions]
    answer_ids = [
        answer.id
        for session in material.sessions
        for answer in session.answers
    ]
    chunk_ids = [chunk.id for chunk in material.chunks]

    if chunk_ids or question_ids or answer_ids:
        db.query(EvidenceLog).filter(
            or_(
                EvidenceLog.chunk_id.in_(chunk_ids or [-1]),
                EvidenceLog.related_question_id.in_(question_ids or [-1]),
                EvidenceLog.related_answer_id.in_(answer_ids or [-1]),
            )
        ).delete(synchronize_session=False)

    if concept_ids or question_ids or session_ids or answer_ids:
        db.query(HintLog).filter(
            or_(
                HintLog.concept_id.in_(concept_ids or [-1]),
                HintLog.question_id.in_(question_ids or [-1]),
                HintLog.session_id.in_(session_ids or [-1]),
                HintLog.user_answer_id.in_(answer_ids or [-1]),
            )
        ).delete(synchronize_session=False)

    if concept_ids:
        db.query(SelfExplanation).filter(SelfExplanation.concept_id.in_(concept_ids)).delete(synchronize_session=False)
    db.query(MaterialMastery).filter(MaterialMastery.material_id == material.id).delete(synchronize_session=False)

    file_path = Path(material.file_path) if material.file_path else None
    db.delete(material)
    db.commit()

    if file_path and file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass


@router.post(
    "/materials/upload",
    response_model=MaterialUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialUploadResponse:
    content = await file.read()
    validate_pdf_upload(file, content)

    file_path = save_upload_file(file, content)
    pages = extract_pdf_pages(content)
    extracted_text = join_page_texts(pages)
    title = Path(file.filename or file_path.name).stem

    material = LearningMaterial(
        user_id=current_user.id,
        title=title,
        file_path=str(file_path),
        extracted_text=extracted_text,
    )
    db.add(material)
    db.flush()
    chunks = build_material_chunks(material.id, pages)
    chunks.extend(
        build_visual_description_chunks(
            material_id=material.id,
            pdf_content=content,
            pages=pages,
            start_index=len(chunks),
        )
    )
    embed_material_chunks(chunks)
    db.add_all(chunks)
    db.commit()
    db.refresh(material)

    return MaterialUploadResponse(
        id=material.id,
        title=material.title,
        file_path=material.file_path,
        extracted_text_length=len(material.extracted_text),
        preview=material.extracted_text[:300],
        created_at=material.created_at,
    )


@router.post("/materials/{material_id}/study/start", response_model=StudyStartResponse)
def start_material_study(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyStartResponse:
    material = db.get(LearningMaterial, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 자료를 찾을 수 없습니다.",
        )
    ensure_material_owner(material, current_user)

    source = "stored"
    concepts = (
        db.query(Concept)
        .filter(Concept.material_id == material.id)
        .order_by(Concept.id.asc())
        .all()
    )
    provider = None

    if not concepts:
        provider = get_llm_provider()
        try:
            source, concepts = extract_and_store_concepts(db, material, provider)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
    concepts = canonical_concepts(concepts)

    session = LearningSession(material_id=material.id, user_id=current_user.id)
    db.add(session)
    db.flush()

    study_items: list[StudyConceptItem] = []
    for concept in concepts:
        normalized_title = base_concept_title(concept.title)
        if concept.title != normalized_title:
            concept.title = normalized_title
        questions = (
            db.query(Question)
            .filter(Question.concept_id == concept.id)
            .order_by(Question.id.asc())
            .all()
        )

        if not questions:
            provider = provider or get_llm_provider()
            try:
                source, questions = generate_and_store_questions(db, concept, provider)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc

        mastery = concept.mastery
        completed = (
            db.query(UserAnswer)
            .join(LearningSession, UserAnswer.session_id == LearningSession.id)
            .filter(
                LearningSession.user_id == current_user.id,
                LearningSession.material_id == material.id,
                UserAnswer.question_id.in_([question.id for question in questions]),
            )
            .count()
            > 0
        )
        study_items.append(
            StudyConceptItem(
                concept=concept,
                question=questions[0],
                difficulty=concept.difficulty,
                hint_budget=hint_budget_for_difficulty(concept.difficulty),
                concept_score=mastery.concept_score if mastery else 0.0,
                tier_name=mastery.tier_name if mastery else "초심자",
                completed=completed,
            )
        )

    material_mastery = update_material_mastery(db, session)
    db.commit()
    db.refresh(session)
    if material_mastery is not None:
        db.refresh(material_mastery)

    return StudyStartResponse(
        session_id=session.id,
        material=MaterialSummaryResponse(
            id=material.id,
            title=material.title,
            extracted_text_length=len(material.extracted_text),
            preview=material.extracted_text[:220],
            created_at=material.created_at,
        ),
        concepts=study_items,
        material_mastery=(
            MaterialMasterySummary(
                material_score=material_mastery.material_score,
                tier_name=material_mastery.tier_name,
                completed_concepts=material_mastery.completed_concepts,
                total_concepts=material_mastery.total_concepts,
            )
            if material_mastery
            else None
        ),
        source=source,
    )
