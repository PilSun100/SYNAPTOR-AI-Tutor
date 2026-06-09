import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def upload_material(client: TestClient, text: str, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/materials/upload",
        files={"file": ("learning.pdf", make_pdf_bytes(text), "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_extract_concepts_from_uploaded_material() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        material_id = upload_material(
            client,
            "Active recall is a learning strategy. "
            "Prediction error helps learners notice misconceptions. "
            "Self explanation improves long-term memory.",
            headers,
        )

        response = client.post(f"/api/materials/{material_id}/concepts/extract", headers=headers)

        body = response.json()
        assert response.status_code == 201
        assert body["material_id"] == material_id
        assert body["source"] in {"heuristic", "gemini"}
        assert body["count"] >= 1
        assert body["concepts"][0]["id"] > 0
        assert body["concepts"][0]["material_id"] == material_id
        assert body["concepts"][0]["title"]
        assert body["concepts"][0]["description"]


def test_extract_concepts_returns_404_for_missing_material() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post("/api/materials/999999/concepts/extract", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "학습 자료를 찾을 수 없습니다."
