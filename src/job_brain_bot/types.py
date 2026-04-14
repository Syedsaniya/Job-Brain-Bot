from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class UserProfile:
    user_id: int
    role: str
    experience: str
    location: str
    skills: list[str] = field(default_factory=list)
    resume_text: str = ""
    alerts_enabled: bool = False


@dataclass(slots=True)
class JobRecord:
    title: str
    company: str
    location: str
    experience: str
    link: str
    source: str
    description: str = ""
    signals: dict[str, str | bool | int] = field(default_factory=dict)
    posted_date: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class MatchResult:
    job_id: int
    total_score: float
    skills_score: float
    experience_score: float
    location_score: float
    keyword_score: float


@dataclass(slots=True)
class AIJobAnalysis:
    """AI analysis result for a job."""

    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str
    role_category: str
    key_responsibilities: list[str]
    soft_skills: list[str]
    certifications_mentioned: list[str]


@dataclass(slots=True)
class SkillGapResult:
    """Skill gap analysis result."""

    matched_skills: list[str]
    missing_skills: list[dict]  # Each with skill, priority, resources
    skill_coverage: float
    recommendation: str
    certifications: list[dict]
    learning_path: list[dict]
    preparation_time: str


@dataclass(slots=True)
class NetworkingMessageResult:
    """Generated networking message."""

    subject: str
    body: str
    tips: list[str]
    follow_up: str
