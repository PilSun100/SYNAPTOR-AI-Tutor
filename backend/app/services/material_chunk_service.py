import re

from app.models.learning import MaterialChunk
from app.services.pdf_service import ExtractedPage

MIN_CHUNK_CHARS = 500
MAX_CHUNK_CHARS = 900


def build_material_chunks(
    material_id: int,
    pages: list[ExtractedPage],
) -> list[MaterialChunk]:
    chunks: list[MaterialChunk] = []
    document_offset = 0
    chunk_index = 0

    for page in pages:
        page_text = _normalize_text(page.text)
        page_offset = document_offset
        local_chunks = _split_page_into_chunks(page_text)

        search_from = 0
        for content in local_chunks:
            local_start = page_text.find(content, search_from)
            if local_start < 0:
                local_start = search_from
            local_end = local_start + len(content)
            search_from = local_end

            chunks.append(
                MaterialChunk(
                    material_id=material_id,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    content=content,
                    char_start=page_offset + local_start,
                    char_end=page_offset + local_end,
                )
            )
            chunk_index += 1

        document_offset += len(page_text) + 2

    return chunks


def _split_page_into_chunks(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text] if text else []

    sentences = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+|\n+", text) if part.strip()]
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not current:
            current = sentence
            continue

        candidate = f"{current} {sentence}"
        if len(candidate) <= MAX_CHUNK_CHARS:
            current = candidate
            continue

        if len(current) >= MIN_CHUNK_CHARS:
            chunks.append(current)
            current = sentence
        else:
            chunks.extend(_hard_split(candidate))
            current = ""

    if current:
        if chunks and len(current) < MIN_CHUNK_CHARS and len(chunks[-1]) + len(current) + 1 <= MAX_CHUNK_CHARS:
            chunks[-1] = f"{chunks[-1]} {current}"
        else:
            chunks.extend(_hard_split(current))

    return chunks


def _hard_split(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARS, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + MIN_CHUNK_CHARS, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        start = end

    return [chunk for chunk in chunks if chunk]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
