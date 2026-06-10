import fitz
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.learning import MaterialChunk
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_upload_material_extracts_text_and_stores_metadata() -> None:
    pdf_bytes = make_pdf_bytes("Active recall strengthens long-term memory.")

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/materials/upload",
            files={"file": ("neuro-learning.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["title"] == "neuro-learning"
        assert body["extracted_text_length"] > 0
        assert "Active recall" in body["preview"]

        with SessionLocal() as db:
            chunks = (
                db.query(MaterialChunk)
                .filter(MaterialChunk.material_id == body["id"])
                .order_by(MaterialChunk.chunk_index.asc())
                .all()
            )
            assert chunks
            assert chunks[0].page_number == 1
            assert chunks[0].chunk_index == 0
            assert chunks[0].chunk_type == "text"
            assert chunks[0].char_start >= 0
            assert chunks[0].char_end > chunks[0].char_start


def test_upload_material_rejects_non_pdf_file() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/materials/upload",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
            headers=headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "PDF 파일만 업로드할 수 있습니다."


def test_list_materials_returns_current_user_uploads() -> None:
    pdf_bytes = make_pdf_bytes("Spaced repetition schedules review before forgetting.")

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("review.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201

        response = client.get("/api/materials", headers=headers)

        body = response.json()
        assert response.status_code == 200
        assert len(body["materials"]) >= 1
        assert body["materials"][0]["title"] == "review"
        assert "Spaced repetition" in body["materials"][0]["preview"]
