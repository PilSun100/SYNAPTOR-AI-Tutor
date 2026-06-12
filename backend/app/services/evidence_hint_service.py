import re

from app.models.learning import Question
from app.services.retrieval_service import RetrievedChunk

KEYWORD_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "개념",
    "설명",
    "자료",
    "자원",
    "가짐",
    "가능",
    "사용",
    "있게",
    "하는",
    "된다",
    "합니다",
    "있습니다",
    "kubernetes",
    "template",
    "템플릿",
}

EXPLANATION_SIGNAL_RE = re.compile(
    r"("
    r"cluster-managed|managed|storage|resource|separate|lifecycle|mount|directly|uses|between|"
    r"reclaiming|retain|delete|recycle|capacity|accessmodes|binding|"
    r"클러스터|관리|스토리지|별개|수명|생명\s*주기|직접|할당|거쳐|반환|정책|삭제|유지|재활용|사용"
    r")",
    re.I,
)

METADATA_RE = re.compile(
    r"("
    r"mobile system engineering|introduction to|semester|"
    r"\btemplate\b|템플릿|"
    r"kubernetes\s*-\s*\d+\s+\d+"
    r")",
    re.I,
)


def build_evidence_hint(
    question: Question,
    evidence_chunks: list[RetrievedChunk],
    hint_level: int,
    stuck_reason: str | None = None,
) -> str:
    points = _key_points(question, evidence_chunks)
    if not points:
        return _fallback_hint(question, hint_level, stuck_reason)

    point_count = min(len(points), 5)
    if hint_level <= 1:
        return _level_one_hint(question, point_count, stuck_reason)
    if hint_level == 2:
        return _level_two_hint(question, points)
    if hint_level == 3:
        return _level_three_hint(question, points)
    if hint_level == 4:
        return _level_four_hint(points)

    return _level_five_hint(points)


def _level_one_hint(question: Question, point_count: int, stuck_reason: str | None) -> str:
    title = _display_title(question)
    if stuck_reason == "question_unclear":
        return f"먼저 질문을 작게 나눠보세요. {title}은/는 무엇을 다루고, 어떤 대상과 관계가 있으며, 자료에서 핵심 특징 {point_count}가지는 무엇인가요?"
    if stuck_reason == "cannot_explain":
        return f"{title}을/를 한 문장으로 정의한 뒤, 자료에서 강조한 특징 {point_count}가지를 붙인다고 생각해보세요."
    if stuck_reason == "confusing_concepts":
        return f"{title}을/를 다른 개념과 비교할 때, 자료의 특징 {point_count}가지를 기준으로 차이를 나눠보세요."
    return f"먼저 스스로 질문해보세요. {title}은/는 무엇을 설명하고, 자료에서 핵심 특징 {point_count}가지는 어떤 의미인가요?"


def _level_two_hint(question: Question, points: list[str]) -> str:
    first = _shorten(points[0])
    rest = [_shorten(point) for point in points[1:3]]
    extra = f" 함께 떠올릴 단서는 {' / '.join(rest)}입니다." if rest else ""
    return (
        "자료 근거 힌트: "
        f"먼저 '{first}'라는 특징을 설명해보세요."
        f"{extra} 이 단서들이 정의, 특징, 사용 방식 중 어디에 들어가는지 연결해보세요."
    )


def _level_three_hint(question: Question, points: list[str]) -> str:
    title = _display_title(question)
    first = _shorten(points[0]) if points else "자료의 첫 번째 특징"
    second = _shorten(points[1]) if len(points) > 1 else "그 특징이 필요한 이유"
    third = _shorten(points[2]) if len(points) > 2 else "자료에서 제시한 사용 방식"
    return (
        "문장 틀 힌트: "
        f"'{title}은/는 {first}이다. "
        f"이 개념의 중요한 특징은 {second}이고, "
        f"실제로는 {third}라는 방식으로 이어진다.' "
        "이 틀을 자기 말로 자연스럽게 바꿔보세요."
    )


def _level_four_hint(points: list[str]) -> str:
    keywords = _keywords_for_points(points)
    return (
        "핵심 키워드 힌트: "
        f"{', '.join(keywords[:6])}. "
        "이 키워드들을 정의, 특징, 사용 방식 순서로 묶어보세요."
    )


def _level_five_hint(points: list[str]) -> str:
    structure = " → ".join(_shorten(point) for point in points[:3])
    return (
        "거의 마지막 힌트입니다. 자료의 설명 구조는 "
        f"{structure} 입니다. "
        "이 구조를 그대로 베끼지 말고, 각 항목이 왜 중요한지 자신의 말로 풀어 설명해보세요."
    )


def _key_points(question: Question, evidence_chunks: list[RetrievedChunk]) -> list[str]:
    title = _display_title(question)
    lines: list[str] = []
    for item in evidence_chunks:
        lines.extend(_learning_lines(item.chunk.content))

    if not lines:
        lines = _learning_lines(question.expected_answer)

    title_tokens = set(_tokens(title))
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        if _is_title_only(line, title):
            continue
        score = _point_score(line, title_tokens)
        if score <= 0:
            continue
        scored.append((score, -index, line))

    if not scored:
        scored = [
            (1, -index, line)
            for index, line in enumerate(lines)
            if not _is_title_only(line, title)
        ]

    scored.sort(reverse=True)
    ordered = sorted(scored[:6], key=lambda item: -item[1])
    return _dedupe_points([line for _, _, line in ordered])[:5]


def _learning_lines(content: str) -> list[str]:
    raw_lines = []
    for raw in content.splitlines():
        expanded = re.sub(
            r"\s+(?=(?:클러스터|Pod|PV)[가-힣A-Za-z]*(?:와|과|에|가|는|은)?\s|(?:Cluster-managed|Separate|Pod\s+does)\b)",
            "\n",
            raw,
        )
        raw_lines.extend(re.split(r"\s*[•·]\s+|\n+", expanded))

    lines = []
    for raw in raw_lines:
        line = re.sub(r"^\[[^\]]+\]\s*", "", raw.strip())
        line = re.sub(r"^[\-–—*•·\d.)\s]+", "", line)
        line = _strip_trailing_slide_footer(line)
        line = re.sub(r"\s+", " ", line).strip()
        if _is_metadata_line(line):
            continue
        if _is_heading_without_explanation(line):
            continue
        if 6 <= len(line) <= 180 and not re.fullmatch(r"\d+", line):
            lines.append(line)
    return lines


def _strip_trailing_slide_footer(line: str) -> str:
    line = re.sub(r"\bKubernetes\s*-\s*\d+\s+\d+\b", "", line, flags=re.I)
    line = re.sub(r"\s+-\s*\d+\s+\d+\s*$", "", line)
    line = re.sub(r"\s+Persistent\s+볼륨\s+생명\s+주기\s*$", "", line)
    line = re.sub(r"\s+Persistent\s+Volume(?:\s+Claim)?\s*[·.\-–—]*\s*$", "", line, flags=re.I)
    return line.strip(" -–—")


def _is_metadata_line(line: str) -> bool:
    normalized = line.lower()
    if not normalized:
        return True
    if METADATA_RE.search(normalized):
        return True
    if _is_slide_title_like(normalized):
        return True
    return bool(re.fullmatch(r"[a-z가-힣\s()_-]{3,45}", normalized, flags=re.I)) and not EXPLANATION_SIGNAL_RE.search(normalized)


def _is_heading_without_explanation(line: str) -> bool:
    tokens = _tokens(line)
    if EXPLANATION_SIGNAL_RE.search(line):
        return False
    if len(tokens) <= 5:
        return True
    return False


def _is_slide_title_like(normalized_line: str) -> bool:
    tokens = set(re.findall(r"[a-z가-힣]+", normalized_line))
    title_tokens = {
        "persistent",
        "volume",
        "claim",
        "pv",
        "pvc",
        "볼륨",
        "생명",
        "주기",
    }
    return bool(tokens) and tokens <= title_tokens


def _point_score(line: str, title_tokens: set[str]) -> int:
    tokens = set(_tokens(line))
    if not tokens:
        return 0

    overlap = len(tokens & title_tokens)
    score = overlap * 3
    if re.search(r"\b(Pod|PVC|PV|volume|storage|policy|prediction|least|squares|algorithm)\b", line, re.I):
        score += 2
    if re.search(r"(관리|별개|수명|생명|주기|할당|거쳐|사용|특징|자원|클러스터)", line):
        score += 2
    if len(tokens) >= 4:
        score += 1
    return score


def _is_title_only(line: str, title: str) -> bool:
    normalized_line = re.sub(r"[^a-z0-9가-힣]+", " ", line.lower()).strip()
    normalized_title = re.sub(r"[^a-z0-9가-힣]+", " ", title.lower()).strip()
    return normalized_line == normalized_title


def _dedupe_points(points: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for point in points:
        key = re.sub(r"[^a-z0-9가-힣]+", " ", point.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(point)
    return deduped


def _keywords_for_points(points: list[str]) -> list[str]:
    keywords = []
    seen = set()
    for point in points:
        for token in _tokens(point):
            if token in KEYWORD_STOPWORDS or token in seen or len(token) < 3:
                continue
            seen.add(token)
            keywords.append(token)
    return keywords or ["자료 근거", "핵심 특징"]


def _shorten(point: str, limit: int = 70) -> str:
    compact = re.sub(r"\s+", " ", point).strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _tokens(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]*|[가-힣]{2,}", text)
        if token.lower() not in KEYWORD_STOPWORDS
    ]


def _display_title(question: Question) -> str:
    title = _strip_trailing_slide_footer(question.concept.title)
    title = re.sub(r"\bKubernetes\s*-\s*\d+(?:\s+\d+)?\b", "", title, flags=re.I)
    title = re.sub(r"\btemplate\b|템플릿", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" -–—")
    return title or question.concept.title


def _fallback_hint(question: Question, hint_level: int, stuck_reason: str | None) -> str:
    title = _display_title(question)
    if hint_level <= 1:
        return f"먼저 {title}이/가 무엇을 설명하는 개념인지 스스로 질문해보세요."
    if stuck_reason == "question_unclear":
        return f"질문을 작게 바꾸면 '{title}은/는 무엇이고 어떤 특징을 가지는가?'입니다."
    if hint_level == 3:
        return f"문장 틀 힌트: '{title}은/는 ...이다. 자료에서는 ... 때문에 중요하다고 설명한다.'"
    if hint_level == 4:
        return f"핵심 키워드 힌트: {title}, 자료 근거, 핵심 특징."
    return f"{title}을/를 자료 근거에 맞춰 정의, 특징, 사용 방식 순서로 설명해보세요."
