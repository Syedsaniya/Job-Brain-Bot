from job_brain_bot.ai_intelligence.skill_gap import GapAnalysis
from job_brain_bot.telegram.formatters import format_skill_gap


def test_format_skill_gap_uses_estimated_preparation_time() -> None:
    gap = GapAnalysis(
        matched_skills=["python"],
        skill_coverage=55.0,
        recommendation="Keep learning",
        estimated_preparation_time="2-3 months",
    )
    text = format_skill_gap(gap)
    assert "2-3 months" in text
