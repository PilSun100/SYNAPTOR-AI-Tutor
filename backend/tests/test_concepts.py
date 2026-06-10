import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.llm_provider import HeuristicProvider
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


def test_heuristic_concept_extraction_filters_slide_metadata() -> None:
    text = """
    Introduction to Reinforcement Learning
    2026. 1st semester
    Mobile System Engineering
    Random Walk Example
    2
    Mobile System Engineering
    Random Walk: MC vs. TD
    4
    Mobile System Engineering
    Advantages and Disadvantages of MC vs. TD (3)
    • TD exploits Markov property
    • MC does not exploit Markov property
    Certainty Equivalence
    • In Batch MC
    • In Batch TD(0)
    Forward-view TD(λ)
    Backward View TD(λ)
    """

    concepts = HeuristicProvider().extract_concepts(text)
    titles = [concept.title for concept in concepts]
    joined_titles = " ".join(titles).lower()

    assert concepts
    assert "introduction to reinforcement learning" not in joined_titles
    assert "mobile system engineering" not in joined_titles
    assert "semester" not in joined_titles
    assert any("Random Walk" in title or "TD" in title for title in titles)
    assert all(concept.difficulty in {"easy", "medium", "hard"} for concept in concepts)
