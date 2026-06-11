from types import SimpleNamespace

from app.services.tier_service import concept_score, is_low_information_answer


def _answer(answer_text: str, correctness_score: float, difficulty: str = "easy"):
    return SimpleNamespace(
        answer_text=answer_text,
        correctness_score=correctness_score,
        question=SimpleNamespace(
            concept=SimpleNamespace(difficulty=difficulty),
        ),
    )


def test_concept_score_is_zero_below_minimum_correctness() -> None:
    score = concept_score(
        _answer("관련 개념을 조금 적었지만 거의 틀린 답변입니다.", 0.09),
        hints_used=0,
    )

    assert score == 0


def test_concept_score_applies_hint_efficiency_only_for_meaningful_scores() -> None:
    no_hint_score = concept_score(
        _answer("Active recall retrieves information before review.", 0.8),
        hints_used=0,
    )
    hinted_score = concept_score(
        _answer("Active recall retrieves information before review.", 0.8),
        hints_used=2,
    )

    assert no_hint_score == 80.0
    assert hinted_score == 64.0
    assert hinted_score < no_hint_score


def test_low_information_detector_flags_placeholder_answers() -> None:
    for answer_text in ["", "  ", "asdf", "test", "몰라", "ㅋㅋㅋㅋㅋㅋ", "aaaaaa", "ㅁㅁㅁㅁ"]:
        assert is_low_information_answer(answer_text)

    assert not is_low_information_answer("개념은 자료에서 설명한 관계와 원인을 연결해 말해야 한다.")
