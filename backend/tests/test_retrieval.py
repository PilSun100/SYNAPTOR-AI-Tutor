import fitz
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.learning import MaterialChunk
from app.services.retrieval_service import retrieve_chunks_by_query
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_retrieve_chunks_by_query_returns_relevant_material_chunks() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={
                "file": (
                    "retrieval.pdf",
                    make_pdf_bytes(
                        "Active recall improves long-term memory by forcing learners "
                        "to retrieve information before checking the material."
                    ),
                    "application/pdf",
                )
            },
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

    with SessionLocal() as db:
        chunks = retrieve_chunks_by_query(db, material_id, "active recall long-term memory")

        assert chunks
        assert chunks[0].chunk.page_number == 1
        assert chunks[0].relevance_score > 0
        assert chunks[0].semantic_score > 0
        assert "Active recall" in chunks[0].chunk.content


def test_upload_stores_material_chunk_embeddings() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={
                "file": (
                    "embedded.pdf",
                    make_pdf_bytes(
                        "Retrieval practice strengthens memory when learners recall "
                        "ideas before reviewing notes."
                    ),
                    "application/pdf",
                )
            },
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

    with SessionLocal() as db:
        chunk = (
            db.query(MaterialChunk)
            .filter(MaterialChunk.material_id == material_id)
            .one()
        )

        assert chunk.embedding
        assert len(chunk.embedding) == 768
        assert chunk.embedding_model


def test_retrieve_chunks_by_query_returns_empty_when_no_evidence_matches() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={
                "file": (
                    "retrieval-empty.pdf",
                    make_pdf_bytes(
                        "Active recall improves long-term memory by forcing learners "
                        "to retrieve information before checking the material."
                    ),
                    "application/pdf",
                )
            },
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

    with SessionLocal() as db:
        chunks = retrieve_chunks_by_query(db, material_id, "zzzzqqq yyyyxxx")

        assert chunks == []
