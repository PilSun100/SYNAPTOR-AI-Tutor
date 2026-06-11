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


def create_study_question(client: TestClient, headers: dict[str, str]) -> tuple[int, int, int]:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "pre-answer-hinting.pdf",
                make_pdf_bytes(
                    "Active recall asks learners to retrieve ideas before review. "
                    "Gradual hints should start small and become more specific."
                ),
                "application/pdf",
            )
        },
        headers=headers,
    )
    assert upload_response.status_code == 201

    material_id = upload_response.json()["id"]
    study_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
    assert study_response.status_code == 200
    body = study_response.json()
    return (
        int(body["session_id"]),
        int(body["concepts"][0]["question"]["id"]),
        int(body["concepts"][0]["hint_budget"]),
    )


def create_persistent_volume_question(client: TestClient, headers: dict[str, str]) -> tuple[int, int]:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "persistent-volume.pdf",
                make_pdf_bytes(
                    "Persistent Volume\n"
                    "Cluster-managed storage volume resource\n"
                    "Separate lifecycle from Pod\n"
                    "Pod does not mount it directly and uses PVC in between"
                ),
                "application/pdf",
            )
        },
        headers=headers,
    )
    assert upload_response.status_code == 201

    material_id = upload_response.json()["id"]
    study_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
    assert study_response.status_code == 200
    body = study_response.json()
    return int(body["session_id"]), int(body["concepts"][0]["question"]["id"])


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
        assert body["hint_budget"] >= 2
        assert body["hints_used"] >= 1
        assert body["hint_text"]
        assert body["evidence"]
        assert body["source"] in {"heuristic", "gemini", "rag"}

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


def test_request_pre_answer_hint_for_question() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        session_id, question_id, hint_budget = create_study_question(client, headers)

        response = client.post(
            f"/api/questions/{question_id}/hint",
            json={
                "session_id": session_id,
                "hint_level": 1,
                "stuck_reason": "forgot_word",
            },
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["user_answer_id"] is None
        assert body["session_id"] == session_id
        assert body["question_id"] == question_id
        assert body["hint_level"] == 1
        assert body["hint_budget"] == hint_budget
        assert body["hints_used"] == 1
        assert body["stuck_reason"] == "forgot_word"
        assert body["hint_text"]
        assert body["evidence"]

        with SessionLocal() as db:
            evidence_count = (
                db.query(EvidenceLog)
                .filter(
                    EvidenceLog.related_question_id == question_id,
                    EvidenceLog.purpose == "pre_answer_hint_generation",
                )
                .count()
            )
            assert evidence_count > 0


def test_pre_answer_hints_use_material_points_progressively() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        session_id, question_id = create_persistent_volume_question(client, headers)

        first = client.post(
            f"/api/questions/{question_id}/hint",
            json={"session_id": session_id, "hint_level": 1},
            headers=headers,
        )
        second = client.post(
            f"/api/questions/{question_id}/hint",
            json={"session_id": session_id, "hint_level": 2},
            headers=headers,
        )
        third = client.post(
            f"/api/questions/{question_id}/hint",
            json={"session_id": session_id, "hint_level": 3},
            headers=headers,
        )

        assert first.status_code == 201
        assert second.status_code == 201
        assert third.status_code == 201
        assert "3가지" in first.json()["hint_text"]
        assert "OOOO" in second.json()["hint_text"]
        assert "Cluster" in second.json()["hint_text"] or "Pod" in second.json()["hint_text"]
        assert "ㅅ" in third.json()["hint_text"] or "V_" in third.json()["hint_text"]
        assert third.json()["source"] == "rag"
