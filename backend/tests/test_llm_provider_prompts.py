from app.services.llm_provider import (
    _build_answer_evaluation_prompt,
    _build_tutor_chat_prompt,
    _parse_tutor_chat,
)


def test_answer_evaluation_prompt_requires_multilingual_semantic_grading() -> None:
    prompt = _build_answer_evaluation_prompt(
        question_text="Explain active recall.",
        expected_answer="Learners retrieve information before seeing the answer.",
        answer_text="정답을 보기 전에 기억에서 정보를 꺼내는 학습 방법입니다.",
        evidence_context="Active recall asks learners to retrieve before review.",
    )

    assert "자료 언어와 답변 언어가 달라도 의미 기준으로 평가" in prompt
    assert "영어 강의자료에 한글 답변" in prompt
    assert "단순 키워드 일치보다 개념 의미" in prompt
    assert "의미 없는 답변" in prompt


def test_tutor_chat_prompt_frames_chat_as_explanation_space() -> None:
    prompt = _build_tutor_chat_prompt(
        user_message="이 개념이 뭐야?",
        evidence_context="Active recall asks learners to retrieve ideas before review.",
    )

    assert "AI Chat은 업로드한 강의자료를 이해하는 설명 공간" in prompt
    assert "Study Room은 사용자가 직접 설명하며 검증받는 공간" in prompt
    assert "개념 설명을 요구하면 근거 범위 안에서 간결하게 설명" in prompt
    assert "답변은 한국어로 작성" in prompt
    assert "3~6문장" in prompt
    assert "Study Room에서 직접 설명해볼 수 있는 질문" in prompt


def test_tutor_chat_parser_wraps_non_json_response() -> None:
    parsed = _parse_tutor_chat("자료에 따르면 active recall은 답을 보기 전에 기억에서 꺼내보는 방식입니다.")

    assert "active recall" in parsed.reply
    assert parsed.learning_mode == "evidence_check"
    assert "Study Room" in parsed.next_action
    assert parsed.suggested_questions
