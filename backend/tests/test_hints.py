import fitz
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.learning import EvidenceLog
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_answer(client: TestClient, headers: dict[str, str]) -> int:
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
        json={"answer_text": "It is about being wrong."},
        headers=headers,
    )
    assert answer_response.status_code == 201
    return int(answer_response.json()["id"])


def test_request_hint_for_answer() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        answer_id = create_answer(client, headers)

        response = client.post(
            f"/api/answers/{answer_id}/hint",
            json={"hint_level": 2},
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["user_answer_id"] == answer_id
        assert body["hint_level"] == 2
        assert body["hint_text"]
        assert body["evidence"]
        assert body["source"] in {"heuristic", "gemini"}

        with SessionLocal() as db:
            evidence_count = (
                db.query(EvidenceLog)
                .filter(
                    EvidenceLog.related_answer_id == answer_id,
                    EvidenceLog.purpose == "hint_generation",
                )
                .count()
            )
            assert evidence_count > 0


def test_request_hint_returns_404_for_missing_answer() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/answers/999999/hint",
            json={"hint_level": 1},
            headers=headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "사용자 답변을 찾을 수 없습니다."


def test_request_hint_rejects_invalid_level() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        answer_id = create_answer(client, headers)

        response = client.post(
            f"/api/answers/{answer_id}/hint",
            json={"hint_level": 6},
            headers=headers,
        )

        assert response.status_code == 422
