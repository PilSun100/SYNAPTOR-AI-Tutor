import fitz
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.learning import EvidenceLog, LearningSession
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def create_question(client: TestClient, headers: dict[str, str]) -> int:
    upload_response = client.post(
        "/api/materials/upload",
        files={
            "file": (
                "answer-evaluation.pdf",
                make_pdf_bytes(
                    "Active recall strengthens memory because learners retrieve "
                    "information before seeing the answer."
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
    return int(question_response.json()["questions"][0]["id"])


def test_submit_answer_evaluates_and_stores_result() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        me = client.get("/api/auth/me", headers=headers).json()
        question_id = create_question(client, headers)

        response = client.post(
            f"/api/questions/{question_id}/answer",
            json={
                "answer_text": "Active recall is retrieving information before seeing the answer.",
                "response_time": 12.5,
            },
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["question_id"] == question_id
        assert body["session_id"] > 0
        assert 0 <= body["correctness_score"] <= 1
        assert body["answer_text"].startswith("Active recall")
        assert body["source"] in {"heuristic", "gemini"}
        assert body["feedback"]
        assert body["hints_used"] == 0
        assert body["hint_budget"] in {3, 4, 5}
        assert 0 <= body["concept_score"] <= 100
        assert body["concept_tier"] in {"초심자", "견습생", "숙련자", "탐구자", "현자"}
        assert body["response_time"] == 12.5
        assert body["adaptive_state"]["learner_level_label"]
        assert body["adaptive_state"]["next_difficulty"] in {"easy", "medium", "hard"}
        assert body["adaptive_state"]["next_question_type"]
        assert body["adaptive_state"]["personalized_explanation"]
        assert body["evidence"]
        assert body["evidence"][0]["chunk_id"] > 0
        assert body["evidence"][0]["page_number"] >= 1
        assert body["evidence"][0]["chunk_type"] == "text"
        assert body["evidence"][0]["snippet"]

        with SessionLocal() as db:
            evidence_count = (
                db.query(EvidenceLog)
                .filter(
                    EvidenceLog.related_answer_id == body["id"],
                    EvidenceLog.purpose == "answer_evaluation",
                )
                .count()
            )
            assert evidence_count > 0
            session = db.get(LearningSession, body["session_id"])
            assert session is not None
            assert session.user_id == me["id"]


def test_submit_answer_returns_404_for_missing_question() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/questions/999999/answer",
            json={"answer_text": "I do not know yet."},
            headers=headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "질문을 찾을 수 없습니다."


def test_submit_answer_links_pre_answer_hints_into_score() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={
                "file": (
                    "hint-aware-score.pdf",
                    make_pdf_bytes("Retrieval practice improves memory when learners answer before review."),
                    "application/pdf",
                )
            },
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]
        study_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
        assert study_response.status_code == 200
        study = study_response.json()
        session_id = study["session_id"]
        question_id = study["concepts"][0]["question"]["id"]

        hint_response = client.post(
            f"/api/questions/{question_id}/hint",
            json={"session_id": session_id, "hint_level": 1},
            headers=headers,
        )
        assert hint_response.status_code == 201

        answer_response = client.post(
            f"/api/questions/{question_id}/answer",
            json={
                "session_id": session_id,
                "answer_text": "Retrieval practice means answering from memory before review.",
            },
            headers=headers,
        )

        body = answer_response.json()
        assert answer_response.status_code == 201
        assert body["hints_used"] == 1
        assert 0 <= body["concept_score"] <= 100
        assert body["material_completed_concepts"] >= 1
        assert body["material_total_concepts"] >= body["material_completed_concepts"]
