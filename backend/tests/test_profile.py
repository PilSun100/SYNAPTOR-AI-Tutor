import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_question_and_concept(client: TestClient, headers: dict[str, str]) -> tuple[int, int]:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "profile-learning.pdf",
                make_pdf_bytes(
                    "Active recall improves durable memory because learners retrieve "
                    "knowledge before reviewing notes. Self explanation reveals gaps "
                    "by forcing learners to connect causes and results."
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
    concept_id = int(concept_response.json()["concepts"][0]["id"])

    question_response = client.post(f"/api/concepts/{concept_id}/questions/generate", headers=headers)
    assert question_response.status_code == 201
    question_id = int(question_response.json()["questions"][0]["id"])
    return question_id, concept_id


def test_learning_profile_returns_default_state_for_new_user() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)

        response = client.get("/api/profile/learning", headers=headers)

        body = response.json()
        assert response.status_code == 200
        assert body["average_recall_score"] == 0
        assert body["best_intervention_type"] == "active_recall"
        assert body["total_answers"] == 0
        assert body["weak_concepts"] == []
        assert body["recommendation_reason"]
        assert body["next_action"]


def test_learning_profile_updates_after_learning_events() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        question_id, concept_id = create_question_and_concept(client, headers)

        answer_response = client.post(
            f"/api/questions/{question_id}/answer",
            json={
                "answer_text": "Active recall means retrieving knowledge before reviewing notes.",
                "response_time": 18,
            },
            headers=headers,
        )
        assert answer_response.status_code == 201
        answer_id = answer_response.json()["id"]

        hint_response = client.post(
            f"/api/answers/{answer_id}/hint",
            json={"hint_level": 1},
            headers=headers,
        )
        assert hint_response.status_code == 201

        explanation_response = client.post(
            f"/api/concepts/{concept_id}/self-explanation",
            json={
                "explanation_text": (
                    "Active recall improves memory because I retrieve knowledge first "
                    "and then compare my answer with the notes."
                )
            },
            headers=headers,
        )
        assert explanation_response.status_code == 201

        profile_response = client.get("/api/profile/learning", headers=headers)

        body = profile_response.json()
        assert profile_response.status_code == 200
        assert body["total_answers"] == 1
        assert body["total_self_explanations"] == 1
        assert 0 <= body["average_recall_score"] <= 1
        assert body["hint_dependency"] == 1
        assert body["best_intervention_type"] in {
            "active_recall",
            "example_first",
            "feynman_check",
            "misconception_repair",
            "mixed_practice",
            "spaced_review",
        }
        assert body["preferred_difficulty_level"] in {"easy", "medium", "hard"}
        assert body["weak_concepts"]
