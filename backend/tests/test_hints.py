import fitz
from fastapi.testclient import TestClient

from app.main import create_app


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_answer(client: TestClient) -> int:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "adaptive-hinting.pdf",
                make_pdf_bytes(
                    "Prediction error occurs when a learner notices the gap "
                    "between their answer and the correct concept."
                ),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 201

    material_id = upload_response.json()["id"]
    concept_response = client.post(f"/api/materials/{material_id}/concepts/extract")
    assert concept_response.status_code == 201

    concept_id = concept_response.json()["concepts"][0]["id"]
    question_response = client.post(f"/api/concepts/{concept_id}/questions/generate")
    assert question_response.status_code == 201

    question_id = question_response.json()["questions"][0]["id"]
    answer_response = client.post(
        f"/api/questions/{question_id}/answer",
        json={"answer_text": "It is about being wrong."},
    )
    assert answer_response.status_code == 201
    return int(answer_response.json()["id"])


def test_request_hint_for_answer() -> None:
    with TestClient(create_app()) as client:
        answer_id = create_answer(client)

        response = client.post(
            f"/api/answers/{answer_id}/hint",
            json={"hint_level": 2},
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["user_answer_id"] == answer_id
        assert body["hint_level"] == 2
        assert body["hint_text"]
        assert body["source"] in {"heuristic", "gemini"}


def test_request_hint_returns_404_for_missing_answer() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/answers/999999/hint",
            json={"hint_level": 1},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "사용자 답변을 찾을 수 없습니다."


def test_request_hint_rejects_invalid_level() -> None:
    with TestClient(create_app()) as client:
        answer_id = create_answer(client)

        response = client.post(
            f"/api/answers/{answer_id}/hint",
            json={"hint_level": 6},
        )

        assert response.status_code == 422
