import logging
from dataclasses import dataclass

import fitz

from app.core.config import settings
from app.models.learning import MaterialChunk
from app.services.pdf_service import ExtractedPage

MAX_VISUAL_PAGES = 12
MIN_VISUAL_DESCRIPTION_CHARS = 40
VISION_MODEL = "gemini-1.5-flash"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    text: str
    image_bytes: bytes


def build_visual_description_chunks(
    material_id: int,
    pdf_content: bytes,
    pages: list[ExtractedPage],
    start_index: int,
) -> list[MaterialChunk]:
    if not settings.gemini_api_key:
        return []

    rendered_pages = _render_candidate_pages(pdf_content, pages)
    chunks: list[MaterialChunk] = []
    chunk_index = start_index

    for rendered in rendered_pages:
        description = _describe_page_visual(rendered)
        if not _is_useful_visual_description(description):
            continue

        chunks.append(
            MaterialChunk(
                material_id=material_id,
                page_number=rendered.page_number,
                chunk_index=chunk_index,
                chunk_type="image_description",
                content=description,
                char_start=0,
                char_end=len(description),
            )
        )
        chunk_index += 1

    return chunks


def _render_candidate_pages(pdf_content: bytes, pages: list[ExtractedPage]) -> list[RenderedPage]:
    text_by_page = {page.page_number: page.text for page in pages}
    try:
        document = fitz.open(stream=pdf_content, filetype="pdf")
    except Exception as exc:
        logger.warning("PDF visual page rendering skipped: %s", exc)
        return []

    rendered_pages: list[RenderedPage] = []
    for index, page in enumerate(document, start=1):
        page_text = text_by_page.get(index, "")
        if not _should_describe_page(page, page_text):
            continue

        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
        rendered_pages.append(
            RenderedPage(
                page_number=index,
                text=page_text,
                image_bytes=pixmap.tobytes("png"),
            )
        )
        if len(rendered_pages) >= MAX_VISUAL_PAGES:
            break

    return rendered_pages


def _should_describe_page(page, page_text: str) -> bool:
    text_length = len(page_text.strip())
    image_count = len(page.get_images(full=True))
    drawing_count = len(page.get_drawings())

    if image_count > 0:
        return True
    if drawing_count >= 5:
        return True
    return text_length < 320 and drawing_count > 0


def _describe_page_visual(rendered: RenderedPage) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(VISION_MODEL)
    prompt = f"""
당신은 강의자료의 도표/그림을 학습 가능한 근거로 변환하는 멀티모달 RAG 모듈입니다.

아래 페이지 이미지를 보고, 학습자가 이해해야 할 그림/도표/수식/표가 있으면 한국어로 설명하세요.

규칙:
- 강의 제목, 과목명, 학기, 페이지 번호, 푸터만 있는 페이지라면 정확히 NO_EDUCATIONAL_VISUAL_CONTENT 라고만 답하세요.
- 실제 공부해야 하는 시각 자료가 있을 때만 설명하세요.
- 이미지에서 확인 가능한 내용만 설명하고, 보이지 않는 내용을 추측하지 마세요.
- 설명은 3~6문장으로 작성하세요.
- 가능하면 "이 그림은 ...을 보여준다", "화살표/축/상태/값은 ...을 의미한다"처럼 학습에 도움이 되게 작성하세요.

페이지 번호: {rendered.page_number}
페이지 텍스트:
{rendered.text[:1200] or "추출된 텍스트 없음"}
""".strip()
    try:
        response = model.generate_content(
            [
                prompt,
                {"mime_type": "image/png", "data": rendered.image_bytes},
            ]
        )
    except Exception as exc:
        logger.warning("PDF visual description skipped for page %s: %s", rendered.page_number, exc)
        return ""

    return (response.text or "").strip()


def _is_useful_visual_description(description: str) -> bool:
    if len(description.strip()) < MIN_VISUAL_DESCRIPTION_CHARS:
        return False
    return "NO_EDUCATIONAL_VISUAL_CONTENT" not in description
