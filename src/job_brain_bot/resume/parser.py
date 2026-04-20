import io
import re
from dataclasses import dataclass

from docx import Document
from pypdf import PdfReader

from job_brain_bot.matching.skill_ontology import get_role_skill_set

COMMON_SKILLS = {
    "python",
    "java",
    "sql",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "linux",
    "git",
    "network security",
    "siem",
    "splunk",
    "power bi",
    "excel",
    "react",
    "node",
}

EXPERIENCE_RE = re.compile(r"(\d+)\s*(?:\+|-|to)?\s*(\d+)?\s*years?", re.IGNORECASE)


@dataclass(slots=True)
class ResumeProfile:
    text: str
    skills: list[str]
    inferred_experience: str
    keywords: list[str]


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _extract_keywords(text: str, limit: int = 30) -> list[str]:
    tokens = [tok.lower() for tok in re.split(r"[^a-zA-Z0-9+#.]+", text) if len(tok) >= 3]
    stopwords = {"the", "and", "with", "for", "from", "you", "your", "that", "have", "are"}
    freq: dict[str, int] = {}
    for token in tokens:
        if token in stopwords:
            continue
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _ in ranked[:limit]]


def _extract_skills(text: str, target_role: str = "") -> list[str]:
    lower = text.lower()
    role_skills = get_role_skill_set(target_role)
    catalog = COMMON_SKILLS | role_skills
    found = [skill for skill in catalog if skill in lower]
    return sorted(found)


def _extract_experience(text: str) -> str:
    matches = EXPERIENCE_RE.findall(text)
    if not matches:
        return ""
    values: list[int] = []
    for low, high in matches:
        values.append(int(low))
        if high:
            values.append(int(high))
    if not values:
        return ""
    low, high = min(values), max(values)
    return f"{low}-{high} years"


def parse_resume_content(filename: str, content: bytes, target_role: str = "") -> ResumeProfile:
    name = filename.lower()
    text = ""
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        text = " ".join((page.extract_text() or "") for page in reader.pages)
    elif name.endswith(".docx"):
        document = Document(io.BytesIO(content))
        text = " ".join(paragraph.text for paragraph in document.paragraphs)
    else:
        text = content.decode("utf-8", errors="ignore")

    normalized = _normalize_text(text)[:20000]
    skills = _extract_skills(normalized, target_role=target_role)
    experience = _extract_experience(normalized)
    keywords = _extract_keywords(normalized)
    return ResumeProfile(
        text=normalized,
        skills=skills,
        inferred_experience=experience,
        keywords=keywords,
    )
