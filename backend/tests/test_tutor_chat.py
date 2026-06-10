import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_tutor_chat_uses_material_evidence() -> None:
    pdf_bytes = make_pdf_bytes(
        "Active recall improves long-term memory because retrieval strengthens learning."
    )

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("active-recall.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        material_id = upload_response.json()["id"]

        response = client.post(
            f"/api/materials/{material_id}/chat",
            json={"message": "Active recall이 왜 중요한지 알려줘"},
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 200
        assert body["material_id"] == material_id
        assert body["reply"]
        assert body["learning_mode"] in {
            "active_recall",
            "feynman_check",
            "misconception_repair",
            "evidence_check",
            "example_first",
        }
        assert body["next_action"]
        assert body["suggested_questions"]
        assert body["evidence"]
        assert body["evidence"][0]["chunk_type"] == "text"
        assert body["source"] in {"gemini", "heuristic"}


def test_tutor_chat_rejects_other_users_material() -> None:
    with TestClient(create_app()) as client:
        owner_headers = auth_headers(client)
        other_headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("private.pdf", make_pdf_bytes("Private concept"), "application/pdf")},
            headers=owner_headers,
        )
        material_id = upload_response.json()["id"]

        response = client.post(
            f"/api/materials/{material_id}/chat",
            json={"message": "이 자료를 설명해줘"},
            headers=other_headers,
        )

        assert response.status_code == 404
