import fitz

from app.services.pdf_service import extract_pdf_pages
from app.services import visual_chunk_service
from app.services.visual_chunk_service import build_visual_description_chunks


def make_visual_pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "TD Backup Diagram")
    page.draw_rect((72, 130, 180, 210))
    page.draw_rect((260, 130, 370, 210))
    page.draw_line((180, 170), (260, 170))
    page.draw_line((250, 160), (260, 170))
    page.draw_line((250, 180), (260, 170))
    return document.tobytes()


def test_visual_chunks_are_skipped_without_vision_api_key() -> None:
    pdf_bytes = make_visual_pdf_bytes()
    pages = extract_pdf_pages(pdf_bytes)

    chunks = build_visual_description_chunks(
        material_id=1,
        pdf_content=pdf_bytes,
        pages=pages,
        start_index=1,
    )

    assert chunks == []


def test_visual_chunks_store_page_aware_descriptions(monkeypatch) -> None:
    pdf_bytes = make_visual_pdf_bytes()
    pages = extract_pdf_pages(pdf_bytes)

    monkeypatch.setattr(visual_chunk_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        visual_chunk_service,
        "_describe_page_visual",
        lambda rendered: "이 그림은 두 상태 박스가 화살표로 연결된 흐름을 보여준다. 학습자는 상태 전이 구조를 이해해야 한다.",
    )

    chunks = build_visual_description_chunks(
        material_id=7,
        pdf_content=pdf_bytes,
        pages=pages,
        start_index=3,
    )

    assert len(chunks) == 1
    assert chunks[0].material_id == 7
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 3
    assert chunks[0].chunk_type == "image_description"
    assert "상태 전이 구조" in chunks[0].content
    assert chunks[0].char_start == 0
    assert chunks[0].char_end == len(chunks[0].content)
