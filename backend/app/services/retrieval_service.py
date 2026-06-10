import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.learning import Concept, EvidenceLog, LearningMaterial, MaterialChunk, Question
from app.schemas.evidence import EvidenceSnippetResponse
from app.services.embedding_service import cosine_similarity, embed_material_chunks, embed_query
from app.services.material_chunk_service import build_material_chunks
from app.services.pdf_service import ExtractedPage

LEXICAL_WEIGHT = 0.45
SEMANTIC_WEIGHT = 0.55
MIN_RELEVANCE_SCORE = 0.015


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: MaterialChunk
    relevance_score: float
    lexical_score: float = 0.0
    semantic_score: float = 0.0


def retrieve_chunks_for_concept(
    db: Session,
    concept_id: int,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    concept = db.get(Concept, concept_id)
    if concept is None:
        return []

    query = f"{concept.title} {concept.description}"
    return retrieve_chunks_by_query(db, concept.material_id, query, top_k=top_k)


def retrieve_chunks_for_question(
    db: Session,
    question_id: int,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    question = db.get(Question, question_id)
    if question is None:
        return []

    query = f"{question.question_text} {question.expected_answer} {question.concept.title}"
    return retrieve_chunks_by_query(db, question.concept.material_id, query, top_k=top_k)


def retrieve_chunks_for_answer(
    db: Session,
    question_id: int,
    user_answer: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    question = db.get(Question, question_id)
    if question is None:
        return []

    query = (
        f"{question.question_text} {question.expected_answer} "
        f"{question.concept.title} {question.concept.description} {user_answer}"
    )
    return retrieve_chunks_by_query(db, question.concept.material_id, query, top_k=top_k)


def retrieve_chunks_by_query(
    db: Session,
    material_id: int,
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    material = db.get(LearningMaterial, material_id)
    if material is None:
        return []

    chunks = _material_chunks(db, material)
    query_embedding = embed_query(query) if any(chunk.embedding for chunk in chunks) else None
    scored = [
        _score_retrieved_chunk(query, query_embedding, chunk)
        for chunk in chunks
    ]
    scored.sort(key=lambda item: (item.relevance_score, -item.chunk.chunk_index), reverse=True)

    positive = [item for item in scored if item.relevance_score >= MIN_RELEVANCE_SCORE]
    return positive[:top_k]


def format_evidence_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "제공된 근거 chunk가 없습니다."

    lines = []
    for item in chunks:
        chunk = item.chunk
        lines.append(
            f"[chunk_id={chunk.id}, page={chunk.page_number}, type={chunk.chunk_type}, "
            f"score={item.relevance_score:.2f}]\n"
            f"{chunk.content[:1200]}"
        )
    return "\n\n".join(lines)


def evidence_snippets(chunks: list[RetrievedChunk]) -> list[EvidenceSnippetResponse]:
    return [
        EvidenceSnippetResponse(
            chunk_id=item.chunk.id,
            page_number=item.chunk.page_number,
            chunk_type=item.chunk.chunk_type,
            snippet=_snippet(item.chunk.content),
            relevance_score=round(item.relevance_score, 3),
        )
        for item in chunks
        if item.relevance_score >= MIN_RELEVANCE_SCORE
    ]


def log_evidence(
    db: Session,
    chunks: list[RetrievedChunk],
    purpose: str,
    related_question_id: int | None = None,
    related_answer_id: int | None = None,
) -> None:
    db.add_all(
        EvidenceLog(
            chunk_id=item.chunk.id,
            purpose=purpose,
            related_question_id=related_question_id,
            related_answer_id=related_answer_id,
            relevance_score=item.relevance_score,
        )
        for item in chunks
        if item.chunk.id is not None and item.relevance_score >= MIN_RELEVANCE_SCORE
    )


def _material_chunks(db: Session, material: LearningMaterial) -> list[MaterialChunk]:
    chunks = (
        db.query(MaterialChunk)
        .filter(MaterialChunk.material_id == material.id)
        .order_by(MaterialChunk.chunk_index.asc())
        .all()
    )
    if chunks:
        return chunks

    fallback_pages = [ExtractedPage(page_number=1, text=material.extracted_text)]
    fallback_chunks = build_material_chunks(material.id, fallback_pages)
    embed_material_chunks(fallback_chunks)
    db.add_all(fallback_chunks)
    db.flush()
    return fallback_chunks


def _score_retrieved_chunk(
    query: str,
    query_embedding: list[float] | None,
    chunk: MaterialChunk,
) -> RetrievedChunk:
    lexical_score = _score_chunk(query, chunk.content)
    semantic_score = cosine_similarity(query_embedding, chunk.embedding)
    if query_embedding and chunk.embedding:
        relevance_score = (lexical_score * LEXICAL_WEIGHT) + (semantic_score * SEMANTIC_WEIGHT)
    else:
        relevance_score = lexical_score

    return RetrievedChunk(
        chunk=chunk,
        relevance_score=round(relevance_score, 4),
        lexical_score=round(lexical_score, 4),
        semantic_score=round(semantic_score, 4),
    )


def _score_chunk(query: str, content: str) -> float:
    query_tokens = _tokens(query)
    content_tokens = _tokens(content)
    if not query_tokens or not content_tokens:
        return 0.0

    query_set = set(query_tokens)
    content_set = set(content_tokens)
    overlap = query_set & content_set
    coverage = len(overlap) / max(len(query_set), 1)
    density = len(overlap) / max(len(content_set), 1)
    phrase_bonus = _phrase_bonus(query, content)
    return round((coverage * 0.7) + (density * 0.2) + phrase_bonus, 4)


def _phrase_bonus(query: str, content: str) -> float:
    normalized_query = " ".join(_tokens(query))
    normalized_content = " ".join(_tokens(content))
    if not normalized_query or not normalized_content:
        return 0.0

    query_phrases = re.findall(r"[A-Za-z가-힣0-9]{3,}(?:\s+[A-Za-z가-힣0-9]{3,})?", normalized_query)
    hits = sum(1 for phrase in query_phrases[:12] if phrase in normalized_content)
    return min(0.12, hits * 0.02)


def _tokens(text: str) -> list[str]:
    stopwords = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "this",
        "from",
        "사용자",
        "질문",
        "답변",
        "개념",
        "설명",
        "합니다",
        "있습니다",
    }
    return [
        token
        for token in re.findall(r"[A-Za-z가-힣0-9]{2,}", text.lower())
        if token not in stopwords
    ]


def _snippet(content: str) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    if len(compact) <= 280:
        return compact
    return f"{compact[:277]}..."
