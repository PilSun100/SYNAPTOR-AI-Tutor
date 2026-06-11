import re

from app.models.learning import Question
from app.services.retrieval_service import RetrievedChunk

HANGUL_BASE = 0xAC00
HANGUL_END = 0xD7A3
CHOSUNG = [
    "ㄱ",
    "ㄲ",
    "ㄴ",
    "ㄷ",
    "ㄸ",
    "ㄹ",
    "ㅁ",
    "ㅂ",
    "ㅃ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅉ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
]

MASK_STOPWORDS = {
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
}


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
        return _level_one_hint(point_count, stuck_reason)
    if hint_level == 2:
        return _format_masked_points(points, mode="blank", max_points=3)
    if hint_level == 3:
        return _format_masked_points(points, mode="initial", max_points=3)
    if hint_level == 4:
        keywords = _keywords_for_points(points)
        return (
            "핵심 키워드 힌트: "
            f"{', '.join(keywords[:6])}. "
            "이 단어들이 각각 어떤 특징을 설명하는지 연결해보세요."
        )

    return (
        "거의 마지막 힌트입니다. 자료의 핵심 구조는 "
        + " / ".join(points[:3])
        + " 입니다. 이 내용을 그대로 읽기보다, 각 항목을 한 문장씩 자신의 말로 바꿔보세요."
    )


def _level_one_hint(point_count: int, stuck_reason: str | None) -> str:
    if stuck_reason == "question_unclear":
        return f"자료에서는 이 개념을 핵심 특징 {point_count}가지로 나눠 설명합니다. 먼저 '무엇인가, 무엇과 분리되는가, 어떻게 쓰는가'처럼 질문을 작게 나눠보세요."
    if stuck_reason == "cannot_explain":
        return f"자료의 핵심 특징은 {point_count}가지입니다. '{'{개념명}'}은/는 ...이고, ...와 분리되며, ...를 통해 사용된다'처럼 문장 틀을 먼저 잡아보세요."
    if stuck_reason == "confusing_concepts":
        return f"자료에서는 비교 기준이 될 특징 {point_count}가지를 제시합니다. 관리 주체, 생명 주기, 연결 방식이 무엇인지 나눠보세요."
    return f"자료에서는 이 개념을 핵심 특징 {point_count}가지로 설명합니다. 각 특징이 무엇을 말하는지 먼저 떠올려보세요."


def _format_masked_points(points: list[str], mode: str, max_points: int) -> str:
    label = "자료 문장 빈칸 힌트" if mode == "blank" else "빈칸 초성 힌트"
    masked = [
        f"{index + 1}. {_mask_point(point, mode)}"
        for index, point in enumerate(points[:max_points])
    ]
    return f"{label}:\n" + "\n".join(masked)


def _key_points(question: Question, evidence_chunks: list[RetrievedChunk]) -> list[str]:
    title = question.concept.title
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
            r"\s+(?=(?:클러스터|Pod|PVC|PV)[가-힣A-Za-z]*(?:와|과|에|가|는|은)?\s|(?:Cluster-managed|Separate|Pod\s+does|PVC\s+in)\b)",
            "\n",
            raw,
        )
        raw_lines.extend(re.split(r"\s*[•·]\s+|\n+", expanded))

    lines = []
    for raw in raw_lines:
        line = re.sub(r"^\[[^\]]+\]\s*", "", raw.strip())
        line = re.sub(r"^[\-–—*•·\d.)\s]+", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if 6 <= len(line) <= 180 and not re.fullmatch(r"\d+", line):
            lines.append(line)
    return lines


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


def _mask_point(point: str, mode: str) -> str:
    matches = list(re.finditer(r"[A-Za-z][A-Za-z0-9-]*|[가-힣]{2,}", point))
    candidates = [
        match
        for match in matches
        if match.group(0).lower() not in MASK_STOPWORDS
        and len(match.group(0)) >= 2
    ]
    if not candidates:
        return point

    targets = candidates[2:] if len(candidates) > 3 else candidates[-1:]
    if not targets:
        targets = candidates[-1:]

    target_spans = {(match.start(), match.end()) for match in targets[:3]}

    parts = []
    cursor = 0
    for match in matches:
        parts.append(point[cursor : match.start()])
        token = match.group(0)
        if (match.start(), match.end()) in target_spans:
            parts.append(_blank_token(token) if mode == "blank" else _initial_token(token))
        else:
            parts.append(token)
        cursor = match.end()
    parts.append(point[cursor:])
    return "".join(parts)


def _blank_token(token: str) -> str:
    length = min(max(len(re.findall(r"[A-Za-z가-힣0-9]", token)), 2), 6)
    return "O" * length


def _initial_token(token: str) -> str:
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", token):
        return token[0].upper() + "_" * min(max(len(token) - 1, 1), 5)
    return "".join(_hangul_initial(char) for char in token)


def _hangul_initial(char: str) -> str:
    code = ord(char)
    if HANGUL_BASE <= code <= HANGUL_END:
        return CHOSUNG[(code - HANGUL_BASE) // 588]
    return char


def _keywords_for_points(points: list[str]) -> list[str]:
    keywords = []
    seen = set()
    for point in points:
        for token in _tokens(point):
            if token in MASK_STOPWORDS or token in seen or len(token) < 3:
                continue
            seen.add(token)
            keywords.append(token)
    return keywords or ["자료 근거", "핵심 특징"]


def _tokens(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]*|[가-힣]{2,}", text)
        if token.lower() not in MASK_STOPWORDS
    ]


def _fallback_hint(question: Question, hint_level: int, stuck_reason: str | None) -> str:
    if hint_level <= 1:
        return "검색된 자료 근거가 충분하지 않습니다. 질문의 개념명과 가장 가까운 슬라이드 제목을 먼저 떠올려보세요."
    if stuck_reason == "question_unclear":
        return f"질문을 작게 바꾸면 '{question.concept.title}은/는 무엇이고 어떤 특징을 가지는가?'입니다."
    return f"{question.concept.title}을/를 설명할 때 자료에서 반복된 핵심 명사와 관계 표현을 먼저 적어보세요."
