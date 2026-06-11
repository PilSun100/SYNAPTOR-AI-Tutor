from sqlalchemy.orm import Session

from app.models.learning import Concept, LearningMaterial
from app.services.concept_normalization_service import base_concept_title, concept_group_key
from app.services.llm_provider import LLMProvider


def extract_and_store_concepts(
    db: Session,
    material: LearningMaterial,
    provider: LLMProvider,
) -> tuple[str, list[Concept]]:
    extracted = _merge_related_concepts(provider.extract_concepts(material.extracted_text))

    concepts_by_title: dict[str, Concept] = {}
    stored_concepts: list[Concept] = []

    for item in extracted:
        concept = Concept(
            material_id=material.id,
            title=item.title,
            description=item.description,
            difficulty=item.difficulty,
        )
        concepts_by_title[item.title] = concept
        stored_concepts.append(concept)

    db.add_all(stored_concepts)
    db.flush()

    for item, concept in zip(extracted, stored_concepts, strict=True):
        if item.parent_title and item.parent_title in concepts_by_title:
            concept.parent_concept_id = concepts_by_title[item.parent_title].id

    db.commit()

    for concept in stored_concepts:
        db.refresh(concept)

    return provider.source, stored_concepts


def _merge_related_concepts(items):
    merged = {}
    order = []
    difficulty_rank = {"easy": 1, "medium": 2, "hard": 3}

    for item in items:
        title = base_concept_title(item.title)
        key = concept_group_key(title)
        if key not in merged:
            merged[key] = {
                "title": title,
                "descriptions": [],
                "difficulty": item.difficulty,
                "parent_title": item.parent_title,
            }
            order.append(key)

        if item.description and item.description not in merged[key]["descriptions"]:
            merged[key]["descriptions"].append(item.description)

        current_rank = difficulty_rank.get(merged[key]["difficulty"], 2)
        next_rank = difficulty_rank.get(item.difficulty, 2)
        if next_rank > current_rank:
            merged[key]["difficulty"] = item.difficulty

    concept_type = type(items[0]) if items else None
    if concept_type is None:
        return []

    return [
        concept_type(
            title=merged[key]["title"],
            description="\n".join(merged[key]["descriptions"]),
            difficulty=merged[key]["difficulty"],
            parent_title=merged[key]["parent_title"],
        )
        for key in order
    ]
