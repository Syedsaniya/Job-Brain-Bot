"""AI-powered job description analyzer.

Extracts structured information from job descriptions using
pattern matching and keyword extraction.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from job_brain_bot.ai_intelligence.skill_ontology_expanded import SKILL_DATABASE


@dataclass(slots=True)
class JobAnalysis:
    """Structured analysis of a job description."""

    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_level: str = ""
    role_category: str = ""
    key_responsibilities: list[str] = field(default_factory=list)
    education_requirements: list[str] = field(default_factory=list)
    certifications_mentioned: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    tools_and_technologies: list[str] = field(default_factory=list)
    domain_knowledge: list[str] = field(default_factory=list)
    salary_keywords: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


# Common skill patterns and variations
SKILL_PATTERNS = {
    "python": [r"\bpython\b", r"\bpy\b"],
    "javascript": [r"\bjavascript\b", r"\bjs\b"],
    "typescript": [r"\btypescript\b", r"\bts\b"],
    "react": [r"\breact\b", r"\breact\.?js\b"],
    "angular": [r"\bangular\b"],
    "vue": [r"\bvue\b", r"\bvue\.?js\b"],
    "node.js": [r"\bnode\.?js\b", r"\bnodejs\b"],
    "sql": [r"\bsql\b", r"\bmysql\b", r"\bpostgresql\b", r"\bsqlite\b"],
    "aws": [r"\baws\b", r"\bamazon web services\b"],
    "azure": [r"\bazure\b", r"\bmicrosoft azure\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "docker": [r"\bdocker\b"],
    "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "linux": [r"\blinux\b", r"\bunix\b"],
    "git": [r"\bgit\b"],
    "ci/cd": [r"\bci/cd\b", r"\bjenkins\b", r"\bgithub actions\b", r"\bgitlab ci\b"],
    "agile": [r"\bagile\b", r"\bscrum\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b", r"\bdeep learning\b"],
    "data analysis": [r"\bdata analysis\b", r"\bdata analytics\b"],
    "communication": [r"\bcommunication\b", r"\binterpersonal\b"],
    "leadership": [r"\bleadership\b", r"\bmanagement\b"],
    "problem solving": [r"\bproblem.?solving\b", r"\banalytical\b"],
}

# Certification patterns
CERTIFICATION_PATTERNS = {
    "aws certified": r"\baws\s+.*\bcertified\b|\bcertified\s+aws\b",
    "azure certified": r"\bazure\s+.*\bcertified\b|\bcertified\s+azure\b",
    "ccna": r"\bccna\b|\bcisco\s+certified\b",
    "ccnp": r"\bccnp\b",
    "ceh": r"\bceh\b|\bcertified\s+ethical\s+hacker\b",
    "cissp": r"\bcissp\b",
    "security+": r"\bsecurity\+\b",
    "pmp": r"\bpmp\b|\bproject\s+management\s+professional\b",
    "scrum master": r"\bscrum\s+master\b|\bcsm\b",
    "itil": r"\bitil\b",
    "cisa": r"\bcisa\b",
    "cism": r"\bcism\b",
    "oscp": r"\boscp\b",
}

# Experience level patterns
EXPERIENCE_PATTERNS = {
    "fresher": r"\b(fresher|entry.?level|graduate|0\s*-\s*1\s*years?)\b",
    "junior": r"\b(junior|jr\.?|1\s*-\s*3\s*years?)\b",
    "mid": r"\b(mid|intermediate|3\s*-\s*5\s*years?)\b",
    "senior": r"\b(senior|sr\.?|5\s*-\s*8\s*years?|8\+?\s*years?)\b",
    "lead": r"\b(lead|principal|staff|architect)\b",
}

# Soft skills patterns
SOFT_SKILLS = [
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "critical thinking",
    "time management",
    "adaptability",
    "creativity",
    "collaboration",
    "presentation",
    "negotiation",
    "mentoring",
]

# Red flag patterns
RED_FLAG_PATTERNS = [
    r"\bunpaid\b.*\binternship\b",
    r"\bwork\s+for\s+equity\b",
    r"\bno\s+salary\b",
    r"\bcommission\s*only\b",
    r"\bunlimited\s+pto\s*.*\bno\s+actual\b",
    r"\brockstar\b.*\bninja\b.*\bguru\b",
    r"\bfast.?paced\b.*\bwear\s+many\s+hats\b",
    r"\bfamily\b.*\bwork\s+environment\b",
]


def extract_skills_from_text(text: str) -> tuple[set[str], set[str]]:
    """Extract required and preferred skills from job description.

    Returns:
        Tuple of (required_skills, preferred_skills)
    """
    text_lower = text.lower()
    required = set()
    preferred = set()

    # Look for skill sections
    required_section = re.search(
        r"(?:required|must have|essential|qualifications?).{0,50}:([^\n]*(?:\n[^\n]*){0,20})",
        text_lower,
        re.IGNORECASE,
    )
    preferred_section = re.search(
        r"(?:preferred|nice to have|bonus|desired).{0,30}:([^\n]*(?:\n[^\n]*){0,15})",
        text_lower,
        re.IGNORECASE,
    )

    required_text = required_section.group(1) if required_section else text_lower
    preferred_text = preferred_section.group(1) if preferred_section else ""

    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, required_text, re.IGNORECASE):
                required.add(skill)
            elif re.search(pattern, preferred_text, re.IGNORECASE):
                preferred.add(skill)
            elif re.search(pattern, text_lower, re.IGNORECASE):
                # If found in general text and not in either section
                if skill not in required and skill not in preferred:
                    required.add(skill)

    return required, preferred


def extract_certifications(text: str) -> list[str]:
    """Extract mentioned certifications from job description."""
    found = []
    text_lower = text.lower()

    for cert, pattern in CERTIFICATION_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.append(cert)

    return found


def extract_experience_level(text: str) -> str:
    """Determine experience level from job description."""
    text_lower = text.lower()

    for level, pattern in EXPERIENCE_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            return level

    # Try to extract years
    years_match = re.search(r"(\d+)\+?\s*years?", text_lower)
    if years_match:
        years = int(years_match.group(1))
        if years <= 1:
            return "fresher"
        elif years <= 3:
            return "junior"
        elif years <= 5:
            return "mid"
        else:
            return "senior"

    return "not specified"


def extract_role_category(title: str, description: str) -> str:
    """Categorize the role based on title and description."""
    text = f"{title} {description}".lower()

    categories = {
        "frontend": ["frontend", "front-end", "ui", "react", "angular", "vue", "css"],
        "backend": ["backend", "back-end", "api", "server", "database", "sql"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
        "devops": ["devops", "sre", "infrastructure", "cloud", "aws", "azure"],
        "cybersecurity": ["security", "cyber", "soc", "pentest", "vulnerability"],
        "data": ["data scientist", "data analyst", "ml engineer", "machine learning"],
        "mobile": ["mobile", "ios", "android", "flutter", "react native"],
        "qa": ["qa", "testing", "automation", "selenium"],
    }

    scores = {cat: sum(1 for kw in keywords if kw in text) for cat, keywords in categories.items()}
    best = max(scores, key=scores.get)

    return best if scores[best] > 0 else "general"


def extract_responsibilities(text: str) -> list[str]:
    """Extract key responsibilities from job description."""
    responsibilities = []

    # Look for responsibilities section
    resp_section = re.search(
        r"(?:responsibilities|what you.ll do|role|duties).{0,30}:([^\n#]*(?:\n[^\n#]*){0,30})",
        text,
        re.IGNORECASE,
    )

    if resp_section:
        section_text = resp_section.group(1)
        # Split by bullet points or numbers
        items = re.split(r"[\n•\-\*]\s*|\d+\.\s*", section_text)
        for item in items:
            item = item.strip()
            if len(item) > 10 and len(item) < 200:
                responsibilities.append(item)

    return responsibilities[:8]  # Limit to 8 items


def extract_education_requirements(text: str) -> list[str]:
    """Extract education requirements."""
    requirements = []
    text_lower = text.lower()

    edu_patterns = [
        r"bachelor'?s?\s+(?:degree)?\s*(?:in)?\s*([^,.\n]+)",
        r"master'?s?\s+(?:degree)?\s*(?:in)?\s*([^,.\n]+)",
        r"phd\s*(?:in)?\s*([^,.\n]+)",
        r"(?:degree|education).{0,20}\b(cs|computer science|engineering|it|information technology|related)\b",
    ]

    for pattern in edu_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        requirements.extend(matches)

    return list(set(requirements))


def extract_soft_skills(text: str) -> list[str]:
    """Extract soft skills mentioned in job description."""
    text_lower = text.lower()
    found = []

    for skill in SOFT_SKILLS:
        if skill in text_lower:
            found.append(skill)

    return found


def detect_red_flags(text: str) -> list[str]:
    """Detect potential red flags in job description."""
    flags = []

    for pattern in RED_FLAG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract context around the match
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                flags.append(context)

    return flags


def analyze_job_description(title: str, description: str) -> JobAnalysis:
    """Analyze a job description and extract structured information.

    Args:
        title: Job title
        description: Full job description text

    Returns:
        JobAnalysis object with extracted information
    """
    full_text = f"{title} {description}"

    required_skills, preferred_skills = extract_skills_from_text(full_text)

    return JobAnalysis(
        required_skills=sorted(required_skills),
        preferred_skills=sorted(preferred_skills),
        experience_level=extract_experience_level(full_text),
        role_category=extract_role_category(title, description),
        key_responsibilities=extract_responsibilities(description),
        education_requirements=extract_education_requirements(description),
        certifications_mentioned=extract_certifications(description),
        soft_skills=extract_soft_skills(description),
        tools_and_technologies=sorted(required_skills | preferred_skills)[:15],
        domain_knowledge=[],  # Would need more sophisticated NLP
        salary_keywords=[],  # Would need salary extraction patterns
        red_flags=detect_red_flags(description),
    )
