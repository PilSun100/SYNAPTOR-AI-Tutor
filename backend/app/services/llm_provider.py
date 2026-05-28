import json
import re
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True)
class ExtractedConcept:
    title: str
    description: str
    difficulty: str = "medium"
    parent_title: str | None = None


@dataclass(frozen=True)
class GeneratedQuestion:
    question_text: str
    question_type: str
    expected_answer: str


@dataclass(frozen=True)
class EvaluatedAnswer:
    correctness_score: float
    missing_points: str
    misconception_detected: bool
    feedback: str


@dataclass(frozen=True)
class GeneratedHint:
    hint_text: str


class LLMProvider(Protocol):
    source: str

    def extract_concepts(self, text: str) -> list[ExtractedConcept]:
        pass

    def generate_questions(
        self,
        concept_title: str,
        concept_description: str,
        material_text: str,
    ) -> list[GeneratedQuestion]:
        pass

    def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
    ) -> EvaluatedAnswer:
        pass

    def generate_hint(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        missing_points: str,
        hint_level: int,
    ) -> GeneratedHint:
        pass


class GeminiProvider:
    source = "gemini"

    def extract_concepts(self, text: str) -> list[ExtractedConcept]:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(_build_concept_prompt(text))
        return _parse_concepts(response.text or "")

    def generate_questions(
        self,
        concept_title: str,
        concept_description: str,
        material_text: str,
    ) -> list[GeneratedQuestion]:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_question_prompt(concept_title, concept_description, material_text)
        )
        return _parse_questions(response.text or "")

    def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
    ) -> EvaluatedAnswer:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_answer_evaluation_prompt(question_text, expected_answer, answer_text)
        )
        return _parse_answer_evaluation(response.text or "")

    def generate_hint(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        missing_points: str,
        hint_level: int,
    ) -> GeneratedHint:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_hint_prompt(
                question_text,
                expected_answer,
                answer_text,
                missing_points,
                hint_level,
            )
        )
        return GeneratedHint(hint_text=(response.text or "").strip())


class HeuristicProvider:
    source = "heuristic"

    def extract_concepts(self, text: str) -> list[ExtractedConcept]:
        chunks = _candidate_chunks(text)
        concepts: list[ExtractedConcept] = []

        for chunk in chunks[:8]:
            title = _make_title(chunk)
            difficulty = "hard" if len(chunk) > 260 else "medium" if len(chunk) > 140 else "easy"
            concepts.append(
                ExtractedConcept(
                    title=title,
                    description=chunk[:500],
                    difficulty=difficulty,
                )
            )

        if not concepts:
            concepts.append(
                ExtractedConcept(
                    title="핵심 개념",
                    description=text[:500],
                    difficulty="medium",
                )
            )

        return concepts

    def generate_questions(
        self,
        concept_title: str,
        concept_description: str,
        material_text: str,
    ) -> list[GeneratedQuestion]:
        context = concept_description or material_text[:500]
        return [
            GeneratedQuestion(
                question_text=f"{concept_title}의 핵심 의미를 자신의 말로 설명해보세요.",
                question_type="definition",
                expected_answer=context,
            ),
            GeneratedQuestion(
                question_text=f"{concept_title}이 학습 과정에서 왜 중요한지 원인과 결과로 설명해보세요.",
                question_type="cause_effect",
                expected_answer=context,
            ),
            GeneratedQuestion(
                question_text=f"{concept_title}을 실제 학습 상황에 적용한 예시를 하나 만들어보세요.",
                question_type="application",
                expected_answer=context,
            ),
        ]

    def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
    ) -> EvaluatedAnswer:
        expected_keywords = set(_keywords(expected_answer))
        answer_keywords = set(_keywords(answer_text))

        if not expected_keywords:
            score = 0.0
            missing = ""
        else:
            matched = expected_keywords & answer_keywords
            score = round(len(matched) / len(expected_keywords), 2)
            missing = ", ".join(sorted(expected_keywords - answer_keywords)[:8])

        misconception_detected = bool(answer_text.strip()) and score < 0.35
        feedback = (
            "핵심 개념을 충분히 포함했습니다."
            if score >= 0.75
            else "일부 핵심 개념이 빠져 있습니다. 빠진 지점을 다시 떠올려보세요."
        )

        return EvaluatedAnswer(
            correctness_score=score,
            missing_points=missing,
            misconception_detected=misconception_detected,
            feedback=feedback,
        )

    def generate_hint(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        missing_points: str,
        hint_level: int,
    ) -> GeneratedHint:
        missing = missing_points or "질문에서 요구한 핵심 조건"
        templates = {
            1: f"방향만 잡아볼게요. 질문이 묻는 핵심 관계가 무엇인지 먼저 떠올려보세요.",
            2: f"관련 개념을 연결해보세요. 특히 {missing} 쪽을 다시 생각해보면 좋습니다.",
            3: "구조를 나눠보세요. 정의, 이유, 결과를 각각 한 문장으로 분리해 답해보세요.",
            4: f"핵심 키워드는 {missing} 입니다. 이 단어들이 답변 안에서 어떤 역할을 하는지 설명해보세요.",
            5: "거의 다 왔습니다. 답변을 '무엇인가 -> 왜 중요한가 -> 어떤 결과가 생기는가' 순서로 다시 구성해보세요.",
        }
        return GeneratedHint(hint_text=templates.get(hint_level, templates[1]))


def get_llm_provider() -> LLMProvider:
    if settings.gemini_api_key:
        return GeminiProvider()
    return HeuristicProvider()


def _build_concept_prompt(text: str) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 개념 구조화 모듈입니다.
아래 학습 자료를 Cognitive Chunking 관점에서 분석해 핵심 개념을 5~8개 추출하세요.

반드시 JSON 배열만 반환하세요. Markdown 코드블록은 쓰지 마세요.
각 항목은 다음 필드를 가져야 합니다.
- title: 개념명
- description: 학습자가 이해해야 할 핵심 설명
- difficulty: easy, medium, hard 중 하나
- parent_title: 상위 개념이 있으면 문자열, 없으면 null

학습 자료:
{text[:12000]}
""".strip()


def _build_question_prompt(
    concept_title: str,
    concept_description: str,
    material_text: str,
) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 Active Recall 질문 생성 모듈입니다.
아래 개념을 보고 학습자가 기억에서 직접 인출해야 하는 질문을 3개 생성하세요.

반드시 JSON 배열만 반환하세요. Markdown 코드블록은 쓰지 마세요.
각 항목은 다음 필드를 가져야 합니다.
- question_text: 학습자에게 보여줄 질문
- question_type: definition, comparison, cause_effect, example, application, misconception 중 하나
- expected_answer: 평가 기준으로 사용할 모범 답안 요약

주의:
- AI가 먼저 설명하는 문장으로 시작하지 마세요.
- 정답을 질문 안에 노출하지 마세요.
- 질문은 한국어로 작성하세요.
- 개념 이해, 적용, 오개념 탐지를 섞으세요.

개념명:
{concept_title}

개념 설명:
{concept_description}

학습 자료 일부:
{material_text[:8000]}
""".strip()


def _build_answer_evaluation_prompt(
    question_text: str,
    expected_answer: str,
    answer_text: str,
) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 답변 평가 모듈입니다.
사용자 답변을 채점하되, 바로 정답을 설명하지 말고 평가 정보만 반환하세요.

반드시 JSON 객체만 반환하세요. Markdown 코드블록은 쓰지 마세요.
필드는 다음과 같습니다.
- correctness_score: 0.0부터 1.0 사이의 숫자
- missing_points: 빠진 핵심 개념을 짧은 문자열로 요약
- misconception_detected: 오개념이 있으면 true, 아니면 false
- feedback: 다음 사고를 유도하는 짧은 피드백. 정답 직접 공개 금지

질문:
{question_text}

평가 기준:
{expected_answer}

사용자 답변:
{answer_text}
""".strip()


def _build_hint_prompt(
    question_text: str,
    expected_answer: str,
    answer_text: str,
    missing_points: str,
    hint_level: int,
) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 Adaptive Scaffolding 모듈입니다.
사용자가 스스로 정답에 도달하도록 힌트를 제공하세요.

힌트 레벨:
1 = 방향 힌트
2 = 관련 개념 힌트
3 = 구조 힌트
4 = 핵심 키워드 힌트
5 = 거의 정답에 가까운 힌트

규칙:
- 정답 문장을 그대로 말하지 마세요.
- 답을 설명하지 말고 다음 사고 행동을 유도하세요.
- 한국어 한두 문장으로 작성하세요.
- 현재 레벨보다 더 강한 힌트를 제공하지 마세요.

질문:
{question_text}

평가 기준:
{expected_answer}

사용자 답변:
{answer_text}

누락된 지점:
{missing_points}

요청 힌트 레벨:
{hint_level}
""".strip()


def _parse_concepts(raw_text: str) -> list[ExtractedConcept]:
    json_text = _extract_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 응답을 JSON으로 해석할 수 없습니다.") from exc

    if not isinstance(data, list):
        raise ValueError("LLM 응답은 JSON 배열이어야 합니다.")

    concepts: list[ExtractedConcept] = []
    for item in data:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()
        description = str(item.get("description", "")).strip()
        difficulty = str(item.get("difficulty", "medium")).strip().lower()
        parent_title = item.get("parent_title")

        if not title or not description:
            continue

        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"

        concepts.append(
            ExtractedConcept(
                title=title[:255],
                description=description,
                difficulty=difficulty,
                parent_title=str(parent_title).strip() if parent_title else None,
            )
        )

    if not concepts:
        raise ValueError("추출된 개념이 없습니다.")

    return concepts


def _parse_questions(raw_text: str) -> list[GeneratedQuestion]:
    json_text = _extract_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 응답을 JSON으로 해석할 수 없습니다.") from exc

    if not isinstance(data, list):
        raise ValueError("LLM 응답은 JSON 배열이어야 합니다.")

    questions: list[GeneratedQuestion] = []
    allowed_types = {
        "definition",
        "comparison",
        "cause_effect",
        "example",
        "application",
        "misconception",
    }

    for item in data:
        if not isinstance(item, dict):
            continue

        question_text = str(item.get("question_text", "")).strip()
        question_type = str(item.get("question_type", "definition")).strip().lower()
        expected_answer = str(item.get("expected_answer", "")).strip()

        if not question_text or not expected_answer:
            continue

        if question_type not in allowed_types:
            question_type = "definition"

        questions.append(
            GeneratedQuestion(
                question_text=question_text,
                question_type=question_type,
                expected_answer=expected_answer,
            )
        )

    if not questions:
        raise ValueError("생성된 질문이 없습니다.")

    return questions


def _parse_answer_evaluation(raw_text: str) -> EvaluatedAnswer:
    json_text = _extract_object_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 응답을 JSON으로 해석할 수 없습니다.") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM 응답은 JSON 객체여야 합니다.")

    score = data.get("correctness_score", 0)
    try:
        correctness_score = max(0.0, min(1.0, float(score)))
    except (TypeError, ValueError):
        correctness_score = 0.0

    return EvaluatedAnswer(
        correctness_score=correctness_score,
        missing_points=str(data.get("missing_points", "")).strip(),
        misconception_detected=bool(data.get("misconception_detected", False)),
        feedback=str(data.get("feedback", "")).strip(),
    )


def _extract_json(raw_text: str) -> str:
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _extract_object_json(raw_text: str) -> str:
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _candidate_chunks(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", compact)
    return [part.strip() for part in parts if len(part.strip()) >= 24]


def _make_title(chunk: str) -> str:
    words = re.findall(r"[A-Za-z0-9가-힣_-]+", chunk)
    if not words:
        return "핵심 개념"
    return " ".join(words[:5])[:80]


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z가-힣]{2,}", text.lower())
    stopwords = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "this",
        "개념",
        "학습",
        "설명",
        "사용자",
        "합니다",
        "있습니다",
    }
    return [word for word in words if word not in stopwords]
