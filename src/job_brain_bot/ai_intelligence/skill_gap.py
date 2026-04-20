"""Skill gap analyzer and learning path recommender.

Analyzes gaps between user skills and job requirements,
suggests certifications and learning resources.
"""

from dataclasses import dataclass, field

from job_brain_bot.ai_intelligence.analyzer import JobAnalysis
from job_brain_bot.ai_intelligence.skill_ontology_expanded import (
    get_career_track,
    get_certification_info,
    get_skill_pathway,
)


@dataclass(slots=True)
class SkillGap:
    """Represents a missing skill with priority and learning resources."""

    skill: str
    priority: str  # "critical", "high", "medium", "low"
    user_has: bool
    job_requires: bool
    learning_hours: int = 0
    resources: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    difficulty: str = "medium"  # "easy", "medium", "hard"


@dataclass(slots=True)
class GapAnalysis:
    """Complete skill gap analysis for a user and job."""

    matched_skills: list[str] = field(default_factory=list)
    missing_critical: list[SkillGap] = field(default_factory=list)
    missing_preferred: list[SkillGap] = field(default_factory=list)
    skill_coverage: float = 0.0  # Percentage of required skills user has
    recommendation: str = ""
    certifications_to_consider: list[dict] = field(default_factory=list)
    learning_path: list[dict] = field(default_factory=list)
    estimated_preparation_time: str = ""


def calculate_skill_match(
    user_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> tuple[set[str], set[str], set[str]]:
    """Calculate skill matches between user and job.

    Returns:
        Tuple of (matched, missing_required, missing_preferred)
    """
    user_set = {s.lower().strip() for s in user_skills if s.strip()}
    required_set = {s.lower().strip() for s in required_skills if s.strip()}
    preferred_set = {s.lower().strip() for s in preferred_skills if s.strip()}

    # Normalize common variations
    normalized_user = set()
    for skill in user_set:
        # Remove common suffixes/prefixes for comparison
        normalized = skill.replace(" programming", "").replace(" development", "")
        normalized_user.add(normalized)
        normalized_user.add(skill)

    matched = set()
    missing_required = set()
    missing_preferred = set()

    for req in required_set:
        # Check exact match
        if req in normalized_user:
            matched.add(req)
        # Check fuzzy match
        elif any(req in u or u in req for u in normalized_user if len(req) > 3):
            matched.add(req)
        else:
            missing_required.add(req)

    for pref in preferred_set:
        if pref in normalized_user or pref in matched:
            matched.add(pref)
        elif any(pref in u or u in pref for u in normalized_user if len(pref) > 3):
            matched.add(pref)
        else:
            missing_preferred.add(pref)

    return matched, missing_required, missing_preferred


def prioritize_missing_skill(skill: str, job_analysis: JobAnalysis) -> str:
    """Determine priority of a missing skill based on job context."""
    skill_lower = skill.lower()

    # Critical skills are often mentioned first or multiple times
    if skill_lower in ["python", "javascript", "sql"]:
        return (
            "critical"
            if skill_lower in [s.lower() for s in job_analysis.required_skills[:3]]
            else "high"
        )

    # Check if skill is in required list (not just preferred)
    if skill_lower in [s.lower() for s in job_analysis.required_skills]:
        return "high"

    # Security skills are high priority for security roles
    if job_analysis.role_category == "cybersecurity":
        security_skills = ["security+", "cissp", "ceh", "penetration testing", "incident response"]
        if any(sec in skill_lower for sec in security_skills):
            return "high"

    # Cloud skills are high priority for devops roles
    if job_analysis.role_category == "devops":
        cloud_skills = ["aws", "azure", "gcp", "docker", "kubernetes"]
        if any(cloud in skill_lower for cloud in cloud_skills):
            return "high"

    return "medium"


def estimate_difficulty(skill: str) -> str:
    """Estimate learning difficulty for a skill."""
    easy_skills = ["git", "html", "css", "basic python", "excel"]
    hard_skills = [
        "kubernetes",
        "machine learning",
        "cissp",
        "system design",
        "penetration testing",
    ]

    skill_lower = skill.lower()

    if any(easy in skill_lower for easy in easy_skills):
        return "easy"
    if any(hard in skill_lower for hard in hard_skills):
        return "hard"

    pathway = get_skill_pathway(skill)
    if pathway:
        if pathway.estimated_hours <= 40:
            return "easy"
        elif pathway.estimated_hours >= 100:
            return "hard"

    return "medium"


def estimate_learning_hours(skill: str) -> int:
    """Estimate hours needed to learn a skill."""
    pathway = get_skill_pathway(skill)
    if pathway:
        return pathway.estimated_hours

    # Default estimates
    defaults = {
        "git": 20,
        "html": 20,
        "css": 40,
        "javascript": 60,
        "python": 80,
        "sql": 40,
        "docker": 30,
        "kubernetes": 80,
        "aws": 120,
        "react": 50,
        "node.js": 50,
        "security+": 60,
        "ceh": 100,
        "cissp": 150,
    }

    return defaults.get(skill.lower(), 50)


def get_learning_resources(skill: str, level: str = "beginner") -> list[str]:
    """Get learning resources for a skill."""
    pathway = get_skill_pathway(skill)
    if not pathway:
        return [f"Search for '{skill} tutorial' on Google/YouTube"]

    resources = []
    if level == "beginner":
        resources = pathway.beginner_resources[:2]
    elif level == "intermediate":
        resources = pathway.intermediate_resources[:2] or pathway.beginner_resources[:2]
    else:
        resources = pathway.advanced_resources[:2] or pathway.intermediate_resources[:2]

    return resources or [f"Official {skill} documentation"]


def get_certification_suggestions(skills: list[str], role_category: str) -> list[dict]:
    """Get certification recommendations based on skills and role."""
    suggestions = []

    career_track = get_career_track(role_category)
    if career_track:
        for cert in career_track.recommended_certifications:
            cert_info = get_certification_info(cert)
            if cert_info:
                suggestions.append(cert_info)

    # Add skill-specific certifications
    for skill in skills:
        pathway = get_skill_pathway(skill)
        if pathway and pathway.certifications:
            for cert in pathway.certifications[:1]:  # Top certification per skill
                cert_info = get_certification_info(cert)
                if cert_info and cert_info not in suggestions:
                    suggestions.append(cert_info)

    return suggestions[:5]  # Limit to top 5


def get_learning_paths(gaps: list[SkillGap], role_category: str) -> list[dict]:
    """Generate learning paths for missing skills."""
    paths = []

    # Sort by priority and difficulty
    sorted_gaps = sorted(
        gaps, key=lambda g: (g.priority != "critical", g.priority != "high", g.difficulty)
    )

    for gap in sorted_gaps[:5]:  # Top 5 gaps
        path = {
            "skill": gap.skill,
            "priority": gap.priority,
            "estimated_hours": gap.learning_hours,
            "difficulty": gap.difficulty,
            "resources": gap.resources[:3],
            "certifications": gap.certifications[:2],
        }
        paths.append(path)

    return paths


def generate_recommendation(
    skill_coverage: float,
    missing_critical: list[SkillGap],
    role_category: str,
) -> str:
    """Generate a personalized recommendation based on gaps."""
    if skill_coverage >= 0.8:
        return (
            "🌟 **Strong Match!** You have most of the required skills. "
            "Focus on getting certifications to stand out from other candidates."
        )
    elif skill_coverage >= 0.6:
        return (
            "✅ **Good Match.** You have the core skills needed. "
            f"Consider learning {len(missing_critical)} critical skills to improve your chances. "
            "This role is within reach with 2-4 weeks of preparation."
        )
    elif skill_coverage >= 0.4:
        return (
            "🟡 **Possible with Preparation.** You have some relevant skills, "
            f"but need to develop {len(missing_critical)} key skills. "
            f"Estimated preparation time: 1-2 months. Consider if this {role_category} path aligns with your goals."
        )
    else:
        return (
            "🟠 **Significant Gap.** This role requires substantial upskilling. "
            f"You'd need to learn {len(missing_critical)} critical skills. "
            "Consider starting with an entry-level position in this field first, "
            "or focus on roles that better match your current skillset."
        )


def analyze_skill_gaps(
    user_skills: list[str],
    job_analysis: JobAnalysis,
) -> GapAnalysis:
    """Analyze skill gaps between user and job requirements.

    Args:
        user_skills: List of skills the user has
        job_analysis: Analysis of the job description

    Returns:
        GapAnalysis with detailed recommendations
    """
    matched, missing_required, missing_preferred = calculate_skill_match(
        user_skills,
        job_analysis.required_skills,
        job_analysis.preferred_skills,
    )

    # Calculate coverage
    total_required = len(job_analysis.required_skills)
    skill_coverage = len(matched) / total_required if total_required > 0 else 1.0

    # Build detailed gap information
    missing_critical = []
    for skill in missing_required:
        priority = prioritize_missing_skill(skill, job_analysis)
        pathway = get_skill_pathway(skill)

        gap = SkillGap(
            skill=skill,
            priority=priority,
            user_has=False,
            job_requires=True,
            learning_hours=estimate_learning_hours(skill),
            resources=get_learning_resources(skill),
            certifications=pathway.certifications[:2] if pathway else [],
            difficulty=estimate_difficulty(skill),
        )
        missing_critical.append(gap)

    missing_preferred_gaps = []
    for skill in missing_preferred:
        pathway = get_skill_pathway(skill)
        gap = SkillGap(
            skill=skill,
            priority="medium",
            user_has=False,
            job_requires=False,
            learning_hours=estimate_learning_hours(skill),
            resources=get_learning_resources(skill),
            certifications=pathway.certifications[:2] if pathway else [],
            difficulty=estimate_difficulty(skill),
        )
        missing_preferred_gaps.append(gap)

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    missing_critical.sort(key=lambda g: priority_order.get(g.priority, 4))

    # Generate learning path
    learning_path = get_learning_paths(missing_critical, job_analysis.role_category)

    # Calculate total preparation time
    total_hours = sum(g.learning_hours for g in missing_critical[:5])
    if total_hours <= 40:
        prep_time = "1-2 weeks"
    elif total_hours <= 80:
        prep_time = "3-6 weeks"
    elif total_hours <= 160:
        prep_time = "2-3 months"
    else:
        prep_time = "3-6 months"

    # Get certification suggestions
    all_missing = [g.skill for g in missing_critical + missing_preferred_gaps]
    certs = get_certification_suggestions(all_missing, job_analysis.role_category)

    return GapAnalysis(
        matched_skills=sorted(matched),
        missing_critical=missing_critical,
        missing_preferred=missing_preferred_gaps,
        skill_coverage=round(skill_coverage * 100, 1),
        recommendation=generate_recommendation(
            skill_coverage, missing_critical, job_analysis.role_category
        ),
        certifications_to_consider=certs,
        learning_path=learning_path,
        estimated_preparation_time=prep_time,
    )


def compare_with_career_track(
    user_skills: list[str],
    role_category: str,
    experience_level: str,
) -> dict:
    """Compare user skills against typical career track requirements."""
    career_track = get_career_track(role_category)
    if not career_track:
        return {"error": f"No career track found for {role_category}"}

    user_set = {s.lower().strip() for s in user_skills if s.strip()}

    # Determine target skills based on experience level
    if experience_level in ["fresher", "junior"]:
        target_skills = career_track.entry_skills
    elif experience_level == "mid":
        target_skills = career_track.mid_skills
    else:
        target_skills = career_track.senior_skills

    target_set = {s.lower().strip() for s in target_skills}

    matched = user_set & target_set
    missing = target_set - user_set

    return {
        "role": career_track.role,
        "experience_level": experience_level,
        "target_skills_count": len(target_set),
        "matched_skills_count": len(matched),
        "coverage": round(len(matched) / len(target_set) * 100, 1) if target_set else 0,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "recommended_certifications": career_track.recommended_certifications,
        "complementary_skills_to_explore": career_track.complementary_skills,
    }
