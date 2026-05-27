from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def validate_pdf_upload(file: UploadFile, content: bytes) -> None:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    if suffix != ".pdf" and file.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드할 수 있습니다.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일은 업로드할 수 없습니다.",
        )

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {settings.max_upload_mb}MB 이하여야 합니다.",
        )


def save_upload_file(file: UploadFile, content: bytes) -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "material.pdf").name
    safe_name = original_name.replace("/", "_").replace("\\", "_")
    target_path = upload_dir / f"{uuid4().hex}_{safe_name}"
    target_path.write_bytes(content)
    return target_path


def extract_pdf_text(content: bytes) -> str:
    try:
        document = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PDF 파일을 읽을 수 없습니다.",
        ) from exc

    page_texts: list[str] = []
    for page in document:
        text = page.get_text("text").strip()
        if text:
            page_texts.append(text)

    extracted_text = "\n\n".join(page_texts).strip()
    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PDF에서 텍스트를 추출할 수 없습니다.",
        )

    return extracted_text
