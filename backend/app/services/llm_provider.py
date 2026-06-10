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


@dataclass(frozen=True)
class EvaluatedSelfExplanation:
    accuracy_score: float
    completeness_score: float
    logical_connection_score: float
    feedback: str


@dataclass(frozen=True)
class GeneratedTutorChat:
    reply: str
    learning_mode: str
    next_action: str
    suggested_questions: list[str]


class LLMProvider(Protocol):
    source: str

    def extract_concepts(self, text: str) -> list[ExtractedConcept]:
        pass

    def generate_questions(
        self,
        concept_title: str,
        concept_description: str,
        material_text: str,
        evidence_context: str = "",
    ) -> list[GeneratedQuestion]:
        pass

    def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        evidence_context: str = "",
    ) -> EvaluatedAnswer:
        pass

    def generate_hint(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        missing_points: str,
        hint_level: int,
        evidence_context: str = "",
    ) -> GeneratedHint:
        pass

    def evaluate_self_explanation(
        self,
        concept_title: str,
        concept_description: str,
        explanation_text: str,
        evidence_context: str = "",
    ) -> EvaluatedSelfExplanation:
        pass

    def generate_tutor_chat(
        self,
        user_message: str,
        evidence_context: str,
    ) -> GeneratedTutorChat:
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
        evidence_context: str = "",
    ) -> list[GeneratedQuestion]:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_question_prompt(concept_title, concept_description, material_text, evidence_context)
        )
        return _parse_questions(response.text or "")

    def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        evidence_context: str = "",
    ) -> EvaluatedAnswer:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_answer_evaluation_prompt(question_text, expected_answer, answer_text, evidence_context)
        )
        return _parse_answer_evaluation(response.text or "")

    def generate_hint(
        self,
        question_text: str,
        expected_answer: str,
        answer_text: str,
        missing_points: str,
        hint_level: int,
        evidence_context: str = "",
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
                evidence_context,
            )
        )
        return GeneratedHint(hint_text=(response.text or "").strip())

    def evaluate_self_explanation(
        self,
        concept_title: str,
        concept_description: str,
        explanation_text: str,
        evidence_context: str = "",
    ) -> EvaluatedSelfExplanation:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            _build_self_explanation_prompt(
                concept_title,
                concept_description,
                explanation_text,
                evidence_context,
            )
        )
        return _parse_self_explanation_evaluation(response.text or "")

    def generate_tutor_chat(
        self,
        user_message: str,
        evidence_context: str,
    ) -> GeneratedTutorChat:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(_build_tutor_chat_prompt(user_message, evidence_context))
        return _parse_tutor_chat(response.text or "")


class HeuristicProvider:
    source = "heuristic"

    def extract_concepts(self, text: str) -> list[ExtractedConcept]:
        chunks = _candidate_chunks(text)
        concepts: list[ExtractedConcept] = []

        for chunk in chunks[:8]:
            title = _make_title(chunk)
            difficulty = _heuristic_difficulty(chunk)
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
        evidence_context: str = "",
    ) -> list[GeneratedQuestion]:
        context = _evidence_or_fallback(evidence_context, concept_description or material_text[:500])
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
        evidence_context: str = "",
    ) -> EvaluatedAnswer:
        evidence_basis = _evidence_or_fallback(evidence_context, expected_answer)
        expected_keywords = set(_keywords(evidence_basis))
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
        evidence_context: str = "",
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

    def evaluate_self_explanation(
        self,
        concept_title: str,
        concept_description: str,
        explanation_text: str,
        evidence_context: str = "",
    ) -> EvaluatedSelfExplanation:
        expected_keywords = set(_keywords(_evidence_or_fallback(evidence_context, concept_description)))
        explanation_keywords = set(_keywords(explanation_text))

        if expected_keywords:
            accuracy = len(expected_keywords & explanation_keywords) / len(expected_keywords)
        else:
            accuracy = 0.0

        word_count = len(_keywords(explanation_text))
        completeness = min(1.0, word_count / 30)
        logical_markers = {"because", "therefore", "so", "why", "그래서", "때문", "따라서", "결과"}
        logical_connection = 1.0 if logical_markers & explanation_keywords else 0.55

        feedback = (
            "자기 설명이 핵심 개념과 잘 연결되어 있습니다."
            if accuracy >= 0.7 and completeness >= 0.6
            else "핵심 키워드와 원인-결과 연결을 더 분명하게 보강해보세요."
        )

        return EvaluatedSelfExplanation(
            accuracy_score=round(accuracy, 2),
            completeness_score=round(completeness, 2),
            logical_connection_score=round(logical_connection, 2),
            feedback=feedback,
        )

    def generate_tutor_chat(
        self,
        user_message: str,
        evidence_context: str,
    ) -> GeneratedTutorChat:
        evidence_basis = _evidence_or_fallback(evidence_context, "")
        evidence_keywords = _keywords(evidence_basis)
        user_keywords = set(_keywords(user_message))
        overlap = [keyword for keyword in evidence_keywords if keyword in user_keywords][:5]

        if not evidence_basis:
            return GeneratedTutorChat(
                reply=(
                    "업로드 자료에서 이 질문을 뒷받침할 근거를 충분히 찾지 못했습니다. "
                    "자료 안의 개념명이나 페이지에 나온 키워드로 다시 질문해보세요."
                ),
                learning_mode="evidence_check",
                next_action="질문에 포함할 핵심 용어를 하나 더 구체화해보세요.",
                suggested_questions=[
                    "이 자료에서 가장 중요한 개념은 무엇인가요?",
                    "방금 질문과 관련된 페이지 근거를 찾아줄 수 있나요?",
                ],
            )

        focus = ", ".join(overlap) if overlap else "검색된 근거"
        return GeneratedTutorChat(
            reply=(
                f"자료 근거 기준으로 보면, 지금 질문은 {focus}와 연결됩니다. "
                "바로 정답을 외우기보다 먼저 그 개념이 어떤 문제를 해결하려는지 한 문장으로 말해보세요. "
                "그다음 근거 문장에서 반복되는 조건, 관계, 결과를 분리하면 이해가 더 안정됩니다."
            ),
            learning_mode="active_recall",
            next_action="근거를 보지 않고 핵심 관계를 한 문장으로 먼저 설명해보세요.",
            suggested_questions=[
                "이 개념을 기억에서 꺼내 한 문장으로 설명해보세요.",
                "자료 근거에서 원인과 결과 관계를 나눠 설명해보세요.",
                "이 개념을 헷갈리기 쉬운 개념과 비교해보세요.",
            ],
        )


def get_llm_provider() -> LLMProvider:
    if settings.gemini_api_key:
        return GeminiProvider()
    return HeuristicProvider()


def _build_concept_prompt(text: str) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 개념 구조화 모듈입니다.
아래 학습 자료를 Cognitive Chunking 관점에서 분석해 핵심 개념을 5~8개 추출하세요.

선별 기준:
- 시험이나 학습에서 설명/비교/적용할 수 있는 실질 개념만 추출하세요.
- 강의 제목, 과목명, 학기, 연도, 페이지 번호, 목차, 발표용 장식 문구는 제외하세요.
- "Introduction to ...", "1st semester", "Mobile System Engineering"처럼 문서 메타데이터에 가까운 항목은 개념으로 만들지 마세요.
- 슬라이드 제목이라도 실제 학습 개념이면 구체적인 개념명으로 정리하세요. 예: "TD exploits Markov property" -> "TD와 Markov property"

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
    evidence_context: str = "",
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
- 아래 제공된 근거 chunk만 사용하세요.
- 근거 chunk로 확인할 수 없는 사실은 만들지 마세요.

개념명:
{concept_title}

개념 설명:
{concept_description}

학습 자료 일부:
{material_text[:8000]}

근거 chunk:
{evidence_context[:8000] or "근거 chunk가 없습니다."}
""".strip()


def _build_answer_evaluation_prompt(
    question_text: str,
    expected_answer: str,
    answer_text: str,
    evidence_context: str = "",
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

엄격한 근거 규칙:
- 반드시 제공된 근거 chunk만 사용하세요.
- 근거 chunk에 없는 내용을 발명하거나 일반 지식으로 보강하지 마세요.
- 정답 전체를 공개하지 말고 능동 회상을 유도하세요.
- missing_points와 misconception_detected는 근거 chunk와 사용자 답변의 차이로만 판단하세요.

질문:
{question_text}

평가 기준:
{expected_answer}

근거 chunk:
{evidence_context[:8000] or "근거 chunk가 없습니다."}

사용자 답변:
{answer_text}
""".strip()


def _build_hint_prompt(
    question_text: str,
    expected_answer: str,
    answer_text: str,
    missing_points: str,
    hint_level: int,
    evidence_context: str = "",
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
- 제공된 근거 chunk만 사용하고, 근거 밖의 정보를 만들지 마세요.

질문:
{question_text}

평가 기준:
{expected_answer}

근거 chunk:
{evidence_context[:8000] or "근거 chunk가 없습니다."}

사용자 답변:
{answer_text}

누락된 지점:
{missing_points}

요청 힌트 레벨:
{hint_level}
""".strip()


def _build_self_explanation_prompt(
    concept_title: str,
    concept_description: str,
    explanation_text: str,
    evidence_context: str = "",
) -> str:
    return f"""
당신은 뇌과학 기반 AI 튜터의 Self-Explanation 평가 모듈입니다.
사용자가 개념을 자신의 언어로 재구성했는지 평가하세요.

반드시 JSON 객체만 반환하세요. Markdown 코드블록은 쓰지 마세요.
필드는 다음과 같습니다.
- accuracy_score: 0.0부터 1.0 사이의 숫자
- completeness_score: 0.0부터 1.0 사이의 숫자
- logical_connection_score: 0.0부터 1.0 사이의 숫자
- feedback: 보완할 사고 방향을 짧게 제시. 정답 전체 공개 금지

근거 규칙:
- 제공된 근거 chunk만 사용하세요.
- 근거 chunk에 없는 내용을 평가 기준으로 삼지 마세요.
- 사용자가 스스로 다시 설명하도록 유도하세요.

개념명:
{concept_title}

개념 설명:
{concept_description}

근거 chunk:
{evidence_context[:8000] or "근거 chunk가 없습니다."}

사용자 자기 설명:
{explanation_text}
""".strip()


def _build_tutor_chat_prompt(user_message: str, evidence_context: str) -> str:
    return f"""
당신은 Brain-Sync의 뇌과학 기반 개인화 AI 튜터입니다.
사용자 질문에 답하되, 일반 챗봇처럼 장황하게 설명하지 말고 업로드 자료 근거를 바탕으로 학습 행동을 설계하세요.

반드시 JSON 객체만 반환하세요. Markdown 코드블록은 쓰지 마세요.
필드는 다음과 같습니다.
- reply: 사용자에게 보여줄 답변. 자료 근거를 요약하되 정답을 모두 공개하기보다 능동 회상을 유도
- learning_mode: active_recall, feynman_check, misconception_repair, evidence_check, example_first 중 하나
- next_action: 사용자가 바로 할 다음 학습 행동 한 문장
- suggested_questions: 사용자가 이어서 물어보거나 답해볼 질문 2~3개 배열

엄격한 근거 규칙:
- 제공된 근거 chunk만 사용하세요.
- 근거 chunk에 없는 내용은 "자료에서 확인되지 않습니다"라고 말하세요.
- 이미지/도표 근거 chunk가 있으면 그것이 시각 자료 설명임을 반영하세요.
- 사용자가 정답을 요구해도 가능한 한 먼저 생각할 단서와 구조를 제공하세요.
- 단, 사용자가 개념 설명을 요구하면 근거 범위 안에서 간결하게 설명하세요.

사용자 질문:
{user_message}

근거 chunk:
{evidence_context[:10000] or "근거 chunk가 없습니다."}
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

        if not title or not description or _is_non_learning_title(title):
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


def _parse_self_explanation_evaluation(raw_text: str) -> EvaluatedSelfExplanation:
    json_text = _extract_object_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 응답을 JSON으로 해석할 수 없습니다.") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM 응답은 JSON 객체여야 합니다.")

    return EvaluatedSelfExplanation(
        accuracy_score=_score(data.get("accuracy_score", 0)),
        completeness_score=_score(data.get("completeness_score", 0)),
        logical_connection_score=_score(data.get("logical_connection_score", 0)),
        feedback=str(data.get("feedback", "")).strip(),
    )


def _parse_tutor_chat(raw_text: str) -> GeneratedTutorChat:
    json_text = _extract_object_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 응답을 JSON으로 해석할 수 없습니다.") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM 응답은 JSON 객체여야 합니다.")

    allowed_modes = {
        "active_recall",
        "feynman_check",
        "misconception_repair",
        "evidence_check",
        "example_first",
    }
    learning_mode = str(data.get("learning_mode", "active_recall")).strip()
    if learning_mode not in allowed_modes:
        learning_mode = "active_recall"

    suggested_questions = data.get("suggested_questions", [])
    if not isinstance(suggested_questions, list):
        suggested_questions = []

    return GeneratedTutorChat(
        reply=str(data.get("reply", "")).strip() or "자료 근거를 바탕으로 다시 질문을 구체화해보세요.",
        learning_mode=learning_mode,
        next_action=str(data.get("next_action", "")).strip() or "핵심 개념을 한 문장으로 먼저 떠올려보세요.",
        suggested_questions=[
            str(question).strip()
            for question in suggested_questions[:3]
            if str(question).strip()
        ],
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
    lines = [_clean_learning_line(line) for line in text.splitlines()]
    meaningful_lines = [line for line in lines if _is_learning_line(line)]
    candidates: list[str] = []
    seen: set[str] = set()

    for index, line in enumerate(meaningful_lines):
        if not _is_candidate_concept_line(line):
            continue

        details = []
        for next_line in meaningful_lines[index + 1 : index + 4]:
            if _is_candidate_concept_line(next_line):
                break
            if _line_score(next_line) > 0:
                details.append(next_line)

        chunk = " ".join([line, *details]).strip()
        normalized = _normalize_title(chunk)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(chunk)

    if not candidates:
        compact = " ".join(meaningful_lines)
        parts = re.split(r"(?<=[.!?。！？])\s+", compact)
        candidates = [part.strip() for part in parts if _is_learning_line(part)]

    return sorted(candidates, key=_candidate_score, reverse=True)[:12]


def _make_title(chunk: str) -> str:
    words = re.findall(r"[A-Za-z0-9가-힣λΛ()_-]+", chunk)
    if not words:
        return "핵심 개념"
    title = " ".join(words[:6])
    title = re.sub(r"\bMobile System Engineering\b", "", title, flags=re.IGNORECASE).strip()
    return title[:80] or "핵심 개념"


def _heuristic_difficulty(chunk: str) -> str:
    score = _line_score(chunk)
    if score >= 9:
        return "hard"
    if score >= 6:
        return "medium"
    return "easy"


def _clean_learning_line(line: str) -> str:
    cleaned = re.sub(r"^[•\-–—·\s]+", "", line.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _is_learning_line(line: str) -> bool:
    if len(line) < 3:
        return False
    if re.fullmatch(r"\d{1,3}", line):
        return False
    if _is_non_learning_title(line):
        return False
    return True


def _is_candidate_concept_line(line: str) -> bool:
    if len(line) < 6:
        return False
    if _line_score(line) <= 0:
        return False
    if line.endswith(":") and len(line.split()) <= 2:
        return False
    return True


def _is_non_learning_title(title: str) -> bool:
    normalized = _normalize_title(title)
    if not normalized:
        return True

    metadata_patterns = [
        r"^introduction to .*\b20\d{2}\b$",
        r"^introduction to reinforcement learning$",
        r"^\d+(st|nd|rd|th)? semester\b",
        r"^mobile system engineering$",
        r"^engineering question$",
        r"^\d+\s+mobile system engineering\b",
        r"^td\s+\d+\s+mobile system engineering\b",
    ]
    if any(re.search(pattern, normalized) for pattern in metadata_patterns):
        return True

    metadata_terms = {"semester", "engineering", "introduction", "question"}
    words = set(re.findall(r"[a-z]+", normalized))
    return bool(words) and words <= metadata_terms


def _candidate_score(text: str) -> int:
    return _line_score(text) * 10 + min(len(_keywords(text)), 12)


def _line_score(text: str) -> int:
    normalized = _normalize_title(text)
    score = 0
    technical_patterns = {
        "reinforcement": 1,
        "random walk": 3,
        "monte": 3,
        "mc": 2,
        "temporal": 3,
        "difference": 2,
        "td": 2,
        "markov": 3,
        "batch": 2,
        "certainty": 3,
        "equivalence": 3,
        "backup": 3,
        "bootstrapping": 3,
        "sampling": 2,
        "dynamic programming": 3,
        "n-step": 3,
        "return": 2,
        "lambda": 3,
        "λ": 3,
        "forward": 2,
        "backward": 2,
        "prediction": 2,
        "value": 2,
    }
    for pattern, weight in technical_patterns.items():
        if pattern in normalized:
            score += weight

    metadata_penalties = ["semester", "mobile system engineering", "introduction to", "question"]
    for pattern in metadata_penalties:
        if pattern in normalized:
            score -= 3

    return score


def _normalize_title(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.replace("λ", "lambda")
    normalized = re.sub(r"[^a-z0-9가-힣()_\-\s]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


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


def _evidence_or_fallback(evidence_context: str, fallback: str) -> str:
    cleaned = evidence_context.strip()
    if cleaned and cleaned != "제공된 근거 chunk가 없습니다.":
        return cleaned
    return fallback


def _score(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0
