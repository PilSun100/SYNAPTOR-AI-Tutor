import hashlib
import math
import re

from app.core.config import settings
from app.models.learning import MaterialChunk


DOCUMENT_TASK_TYPE = "retrieval_document"
QUERY_TASK_TYPE = "retrieval_query"
LOCAL_EMBEDDING_MODEL = "local-hashing-embedding"


def embed_material_chunks(chunks: list[MaterialChunk]) -> None:
    for chunk in chunks:
        chunk.embedding = embed_document(chunk.content)
        chunk.embedding_model = _active_model_name()


def embed_document(text: str) -> list[float]:
    return _embed_text(text, task_type=DOCUMENT_TASK_TYPE)


def embed_query(text: str) -> list[float]:
    return _embed_text(text, task_type=QUERY_TASK_TYPE)


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right:
        return 0.0

    limit = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(limit))
    left_norm = math.sqrt(sum(value * value for value in left[:limit]))
    right_norm = math.sqrt(sum(value * value for value in right[:limit]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def _embed_text(text: str, task_type: str) -> list[float]:
    if settings.gemini_api_key:
        try:
            return _gemini_embedding(text, task_type)
        except Exception:
            if settings.is_production:
                raise

    return _local_embedding(text)


def _gemini_embedding(text: str, task_type: str) -> list[float]:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    response = genai.embed_content(
        model=settings.embedding_model,
        content=text[:8000],
        task_type=task_type,
    )
    embedding = response.get("embedding") if isinstance(response, dict) else None
    if not embedding:
        raise ValueError("Gemini embedding 응답에 embedding 값이 없습니다.")
    return [float(value) for value in embedding]


def _local_embedding(text: str) -> list[float]:
    vector = [0.0] * settings.embedding_dimensions
    tokens = re.findall(r"[A-Za-z가-힣0-9]{2,}", text.lower())
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % settings.embedding_dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def _active_model_name() -> str:
    if settings.gemini_api_key:
        return settings.embedding_model
    return LOCAL_EMBEDDING_MODEL
