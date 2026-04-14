"""AI Intelligence Layer for Job Brain Bot.

Provides job description analysis, skill gap identification,
and networking message generation.
"""

from job_brain_bot.ai_intelligence.analyzer import analyze_job_description
from job_brain_bot.ai_intelligence.skill_gap import (
    analyze_skill_gaps,
    get_certification_suggestions,
    get_learning_paths,
)
from job_brain_bot.ai_intelligence.networking import (
    generate_cold_message,
    generate_referral_request,
)

__all__ = [
    "analyze_job_description",
    "analyze_skill_gaps",
    "get_certification_suggestions",
    "get_learning_paths",
    "generate_cold_message",
    "generate_referral_request",
]
