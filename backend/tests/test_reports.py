import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_learning_flow(client: TestClient, headers: dict[str, str]) -> tuple[int, int, int]:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "session-report.pdf",
                make_pdf_bytes(
                    "Active recall strengthens long-term memory because learners "
                    "retrieve information before seeing the answer. Self explanation "
                    "helps learners reconstruct ideas in their own words."
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
            "answer_text": "Active recall retrieves information before seeing the answer.",
            "response_time": 9.0,
        },
        headers=headers,
    )
    assert answer_response.status_code == 201
    session_id = answer_response.json()["session_id"]
    answer_id = answer_response.json()["id"]

    hint_response = client.post(
        f"/api/answers/{answer_id}/hint",
        json={"hint_level": 1},
        headers=headers,
    )
    assert hint_response.status_code == 201

    self_explanation_response = client.post(
        f"/api/concepts/{concept_id}/self-explanation",
        json={
            "explanation_text": (
                "Active recall helps memory because I retrieve information first "
                "and then connect the result with my own explanation."
            )
        },
        headers=headers,
    )
    assert self_explanation_response.status_code == 201

    return session_id, material_id, concept_id


def test_get_session_report_returns_learning_summary() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        session_id, material_id, concept_id = create_learning_flow(client, headers)

        response = client.get(f"/api/sessions/{session_id}/report", headers=headers)

        body = response.json()
        assert response.status_code == 200
        assert body["session_id"] == session_id
        assert body["material_id"] == material_id
        assert body["total_answers"] == 1
        assert 0 <= body["average_score"] <= 1
        assert body["studied_concepts"][0]["concept_id"] == concept_id
        assert isinstance(body["self_correct_concepts"], list)
        assert isinstance(body["hinted_correct_concepts"], list)
        assert isinstance(body["repeated_wrong_concepts"], list)
        assert body["next_review_concepts"]
        assert body["adaptive_summary"]
        assert body["adaptive_summary"][0]["learner_level_label"]
        assert body["studied_concepts"][0]["next_question_type"]


def test_get_session_report_returns_404_for_missing_session() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.get("/api/sessions/999999/report", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "학습 세션을 찾을 수 없습니다."
