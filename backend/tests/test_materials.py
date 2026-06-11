import fitz
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.learning import Concept, LearningMaterial, MaterialChunk, Question
from auth_helpers import auth_headers


def make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_upload_material_extracts_text_and_stores_metadata() -> None:
    pdf_bytes = make_pdf_bytes("Active recall strengthens long-term memory.")

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/materials/upload",
            files={"file": ("neuro-learning.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )

        body = response.json()
        assert response.status_code == 201
        assert body["id"] > 0
        assert body["title"] == "neuro-learning"
        assert body["extracted_text_length"] > 0
        assert "Active recall" in body["preview"]

        with SessionLocal() as db:
            chunks = (
                db.query(MaterialChunk)
                .filter(MaterialChunk.material_id == body["id"])
                .order_by(MaterialChunk.chunk_index.asc())
                .all()
            )
            assert chunks
            assert chunks[0].page_number == 1
            assert chunks[0].chunk_index == 0
            assert chunks[0].chunk_type == "text"
            assert chunks[0].char_start >= 0
            assert chunks[0].char_end > chunks[0].char_start


def test_upload_material_rejects_non_pdf_file() -> None:
    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/materials/upload",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
            headers=headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "PDF 파일만 업로드할 수 있습니다."


def test_list_materials_returns_current_user_uploads() -> None:
    pdf_bytes = make_pdf_bytes("Spaced repetition schedules review before forgetting.")

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("review.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201

        response = client.get("/api/materials", headers=headers)

        body = response.json()
        assert response.status_code == 200
        assert len(body["materials"]) >= 1
        assert body["materials"][0]["title"] == "review"
        assert "Spaced repetition" in body["materials"][0]["preview"]


def test_delete_material_removes_current_user_material() -> None:
    pdf_bytes = make_pdf_bytes("Deletion should remove this material and its generated study data.")

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("delete-me.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        study_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
        assert study_response.status_code == 200

        response = client.delete(f"/api/materials/{material_id}", headers=headers)
        assert response.status_code == 204

        list_response = client.get("/api/materials", headers=headers)
        listed_ids = [item["id"] for item in list_response.json()["materials"]]
        assert material_id not in listed_ids

        with SessionLocal() as db:
            assert db.get(LearningMaterial, material_id) is None
            assert db.query(Concept).filter(Concept.material_id == material_id).count() == 0
            assert db.query(MaterialChunk).filter(MaterialChunk.material_id == material_id).count() == 0


def test_delete_material_rejects_other_users_material() -> None:
    pdf_bytes = make_pdf_bytes("Only the owner can delete this material.")

    with TestClient(create_app()) as client:
        owner_headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("private-delete.pdf", pdf_bytes, "application/pdf")},
            headers=owner_headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        other_headers = auth_headers(client)
        response = client.delete(f"/api/materials/{material_id}", headers=other_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "학습 자료를 찾을 수 없습니다."

        with SessionLocal() as db:
            assert db.get(LearningMaterial, material_id) is not None


def test_start_material_study_prepares_first_question() -> None:
    pdf_bytes = make_pdf_bytes(
        "Active recall asks learners to retrieve an idea before reading the answer. "
        "Hints should be gradual so learners still think first."
    )

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("study-start.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)

        body = response.json()
        assert response.status_code == 200
        assert body["session_id"] > 0
        assert body["material"]["id"] == material_id
        assert body["concepts"]
        assert body["concepts"][0]["concept"]["id"] > 0
        assert body["concepts"][0]["question"]["question_text"]
        assert body["concepts"][0]["hint_budget"] in {3, 4, 5}
        assert body["concepts"][0]["tier_name"] in {"초심자", "견습생", "숙련자", "탐구자", "현자"}
        assert body["source"] in {"heuristic", "gemini", "stored"}


def test_start_material_study_reuses_existing_concepts_and_questions() -> None:
    pdf_bytes = make_pdf_bytes(
        "Self explanation reveals understanding gaps because learners must connect causes, "
        "conditions, and results in their own words."
    )

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("reuse-study.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        first_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
        assert first_response.status_code == 200

        with SessionLocal() as db:
            concept_count = db.query(Concept).filter(Concept.material_id == material_id).count()
            question_count = (
                db.query(Question)
                .join(Concept, Question.concept_id == Concept.id)
                .filter(Concept.material_id == material_id)
                .count()
            )

        second_response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)
        assert second_response.status_code == 200

        with SessionLocal() as db:
            assert db.query(Concept).filter(Concept.material_id == material_id).count() == concept_count
            assert (
                db.query(Question)
                .join(Concept, Question.concept_id == Concept.id)
                .filter(Concept.material_id == material_id)
                .count()
                == question_count
            )


def test_start_material_study_hides_other_users_materials() -> None:
    pdf_bytes = make_pdf_bytes("Misconception checks compare the answer with material evidence.")

    with TestClient(create_app()) as client:
        owner_headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("private-study.pdf", pdf_bytes, "application/pdf")},
            headers=owner_headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        other_headers = auth_headers(client)
        response = client.post(f"/api/materials/{material_id}/study/start", headers=other_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "학습 자료를 찾을 수 없습니다."


def test_start_material_study_merges_numbered_concept_parts() -> None:
    pdf_bytes = make_pdf_bytes(
        "Linear Least Squares Prediction Algorithms (1)\n"
        "LSTD estimates value function weights from sampled transitions.\n"
        "Linear Least Squares Prediction Algorithms (2)\n"
        "LSTD uses a least-squares fixed point equation for prediction."
    )

    with TestClient(create_app()) as client:
        headers = auth_headers(client)
        upload_response = client.post(
            "/api/materials/upload",
            files={"file": ("numbered-concepts.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 201
        material_id = upload_response.json()["id"]

        response = client.post(f"/api/materials/{material_id}/study/start", headers=headers)

        body = response.json()
        titles = [item["concept"]["title"] for item in body["concepts"]]
        assert response.status_code == 200
        assert "Linear Least Squares Prediction Algorithms" in titles
        assert "Linear Least Squares Prediction Algorithms (1)" not in titles
        assert "Linear Least Squares Prediction Algorithms (2)" not in titles
