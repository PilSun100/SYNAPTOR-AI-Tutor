import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_dashboard_learning_event(client: TestClient, headers: dict[str, str]) -> None:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "dashboard-learning.pdf",
                make_pdf_bytes(
                    "Active recall strengthens memory when learners retrieve knowledge "
                    "before reviewing notes. Prediction error helps learners notice gaps "
                    "between their answer and evidence from the material."
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
    concept_id = concept_response.json()["concepts"][0]["id"]

    question_response = client.post(f"/api/concepts/{concept_id}/questions/generate", headers=headers)
    assert question_response.status_code == 201
    question_id = question_response.json()["questions"][0]["id"]

    answer_response = client.post(
        f"/api/questions/{question_id}/answer",
        json={
            "answer_text": "Active recall is just rereading notes repeatedly.",
            "response_time": 35,
        },
        headers=headers,
    )
    assert answer_response.status_code == 201


def test_dashboard_summary_returns_default_state_for_new_user() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)

        response = client.get("/api/dashboard/summary", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["profile"]["total_answers"] == 0
        assert body["daily_review"]["review_items"] == []
        assert body["memory_summary"]["total_materials"] == 0
        assert body["memory_summary"]["total_concepts"] == 0
        assert body["misconception_notes"] == []
        assert body["review_schedule"] == []
        assert body["recent_sessions"] == []


def test_dashboard_summary_reflects_learning_events() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        create_dashboard_learning_event(client, headers)

        response = client.get("/api/dashboard/summary", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["profile"]["total_answers"] == 1
        assert body["memory_summary"]["total_materials"] == 1
        assert body["memory_summary"]["total_concepts"] >= 1
        assert body["memory_summary"]["weak_concept_count"] >= 1
        assert body["daily_review"]["review_items"]
        assert body["review_schedule"]
        assert body["recent_sessions"]
        assert body["recent_sessions"][0]["total_answers"] == 1
        assert 0 <= body["recent_sessions"][0]["average_score"] <= 1
