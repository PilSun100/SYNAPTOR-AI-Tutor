import re

from app.models.learning import Concept


def base_concept_title(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", title).strip()
    cleaned = re.sub(r"\s*\((?:part\s*)?\d+[)\.]?\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:part|section)\s+\d+\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+$", "", cleaned)
    return cleaned.strip(" -_:") or title.strip()


def concept_group_key(title: str) -> str:
    normalized = base_concept_title(title).lower()
    normalized = normalized.replace("λ", "lambda")
    normalized = re.sub(r"[^a-z0-9가-힣]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def canonical_concepts(concepts: list[Concept]) -> list[Concept]:
    grouped: dict[str, Concept] = {}
    for concept in concepts:
        key = concept_group_key(concept.title)
        if not key:
            key = str(concept.id)
        grouped.setdefault(key, concept)
    return list(grouped.values())
