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
                "self-explanation.pdf",
                make_pdf_bytes(
                    "Self explanation improves long-term memory because learners "
                    "reconstruct concepts in their own words and connect causes "
                    "with results."
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


def test_submit_self_explanation_updates_mastery() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        concept_id = create_concept(client, headers)

        response = client.post(
            f"/api/concepts/{concept_id}/self-explanation",
            json={
                "explanation_text": (
                    "Self explanation helps memory because I reconstruct the concept "
                    "in my own words and connect the cause with the result."
                )
            },
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["concept_id"] == concept_id
        assert 0 <= body["accuracy_score"] <= 1
        assert 0 <= body["completeness_score"] <= 1
        assert 0 <= body["logical_connection_score"] <= 1
        assert 0 <= body["mastery_level"] <= 1
        assert body["next_review_at"]
        assert body["feedback"]
        assert body["adaptive_state"]["learner_level_label"]
        assert body["adaptive_state"]["recommended_strategy"]
        assert body["source"] in {"heuristic", "gemini"}


def test_submit_self_explanation_returns_404_for_missing_concept() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/concepts/999999/self-explanation",
            json={"explanation_text": "This explanation is long enough."},
            headers=headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "개념을 찾을 수 없습니다."


def test_submit_self_explanation_rejects_too_short_text() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        concept_id = create_concept(client, headers)

        response = client.post(
            f"/api/concepts/{concept_id}/self-explanation",
            json={"explanation_text": "short"},
            headers=headers,
        )

        assert response.status_code == 422
