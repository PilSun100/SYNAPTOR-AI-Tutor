from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import LearningMaterial, User
from app.schemas.materials import MaterialUploadResponse
from app.services.embedding_service import embed_material_chunks
from app.services.material_chunk_service import build_material_chunks
from app.services.pdf_service import extract_pdf_pages, join_page_texts, save_upload_file, validate_pdf_upload
from app.services.visual_chunk_service import build_visual_description_chunks

router = APIRouter()


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
