from app.services.llm_provider import _build_answer_evaluation_prompt


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
