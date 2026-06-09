import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_concept(client: TestClient, headers: dict[str, str]) -> int:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "active-recall.pdf",
                make_pdf_bytes(
                    "Active recall requires learners to retrieve information "
                    "before seeing the answer. It strengthens memory."
                ),
                "application/pdf",
            )
        },
        headers=headers,
    )
    assert upload_response.status_code == 201

    material_id = upload_response.json()["id"]
    concept_response = client.post(f"/api/materials/{material_id}/concepts/extract", headers=headers)
    assert concept_response.status_code == 201
    return int(concept_response.json()["concepts"][0]["id"])


def test_generate_questions_for_concept() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        concept_id = create_concept(client, headers)

        response = client.post(f"/api/concepts/{concept_id}/questions/generate", headers=headers)

        body = response.json()
        assert response.status_code == 201
        assert body["concept_id"] == concept_id
        assert body["source"] in {"heuristic", "gemini"}
        assert body["count"] >= 1
        assert body["questions"][0]["id"] > 0
        assert body["questions"][0]["concept_id"] == concept_id
        assert body["questions"][0]["question_text"]
        assert body["questions"][0]["expected_answer"]


def test_generate_questions_returns_404_for_missing_concept() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post("/api/concepts/999999/questions/generate", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "개념을 찾을 수 없습니다."
