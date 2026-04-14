"""Tests for skill gap analysis module."""

import pytest

from job_brain_bot.ai_intelligence.analyzer import JobAnalysis, analyze_job_description
from job_brain_bot.ai_intelligence.skill_gap import (
    GapAnalysis,
    SkillGap,
    analyze_skill_gaps,
    calculate_skill_match,
    estimate_learning_hours,
    get_certification_suggestions,
    get_learning_resources,
    prioritize_missing_skill,
)


def test_calculate_skill_match_basic():
    """Test basic skill matching."""
    user = ["python", "sql"]
    required = ["python", "sql", "aws"]
    preferred = ["docker"]

    matched, missing_req, missing_pref = calculate_skill_match(user, required, preferred)

    assert len(matched) == 2
    assert "aws" in missing_req
    assert "docker" in missing_pref


def test_calculate_skill_match_no_overlap():
    """Test skill matching with no common skills."""
    user = ["javascript"]
    required = ["python", "sql"]
    preferred = ["aws"]

    matched, missing_req, missing_pref = calculate_skill_match(user, required, preferred)

    assert len(matched) == 0
    assert "python" in missing_req
    assert "sql" in missing_req


def test_calculate_skill_match_case_insensitive():
    """Test case insensitive matching."""
    user = ["Python", "AWS"]
    required = ["python", "aws"]
    preferred = []

    matched, missing_req, missing_pref = calculate_skill_match(user, required, preferred)

    assert len(matched) == 2
    assert len(missing_req) == 0


def test_prioritize_missing_skill_critical():
    """Test critical skill prioritization."""
    job = JobAnalysis(
        required_skills=["python", "sql", "aws"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    priority = prioritize_missing_skill("python", job)
    assert priority in ["critical", "high"]


def test_prioritize_missing_skill_security():
    """Test security skill prioritization."""
    job = JobAnalysis(
        required_skills=[],
        preferred_skills=[],
        experience_level="",
        role_category="cybersecurity",
    )

    priority = prioritize_missing_skill("incident response", job)
    assert priority == "high"


def test_estimate_learning_hours_known_skill():
    """Test learning hour estimation for known skills."""
    hours = estimate_learning_hours("python")
    assert hours > 0
    assert isinstance(hours, int)


def test_estimate_learning_hours_unknown_skill():
    """Test learning hour estimation for unknown skills."""
    hours = estimate_learning_hours("unknown_skill_xyz")
    assert hours > 0  # Should return default value


def test_get_learning_resources_returns_list():
    """Test that learning resources returns a list."""
    resources = get_learning_resources("python")
    assert isinstance(resources, list)
    assert len(resources) > 0


def test_get_learning_resources_unknown_skill():
    """Test learning resources for unknown skill."""
    resources = get_learning_resources("unknown_skill")
    assert isinstance(resources, list)
    assert len(resources) > 0  # Should return generic resource


def test_get_certification_suggestions_security():
    """Test certification suggestions for security role."""
    suggestions = get_certification_suggestions(["security", "python"], "cybersecurity")

    assert isinstance(suggestions, list)
    # Should include security-related certs
    assert len(suggestions) > 0


def test_get_certification_suggestions_devops():
    """Test certification suggestions for devops role."""
    suggestions = get_certification_suggestions(["docker", "aws"], "devops")

    assert isinstance(suggestions, list)


def test_analyze_skill_gaps_structure():
    """Test that analyze_skill_gaps returns proper structure."""
    user_skills = ["python", "sql"]
    job_analysis = JobAnalysis(
        required_skills=["python", "sql", "aws"],
        preferred_skills=["docker"],
        experience_level="mid",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    assert isinstance(result, GapAnalysis)
    assert result.skill_coverage > 0
    assert result.recommendation != ""


def test_analyze_skill_gaps_calculates_coverage():
    """Test that skill coverage is calculated correctly."""
    user_skills = ["python", "sql"]  # 2 out of 3 required
    job_analysis = JobAnalysis(
        required_skills=["python", "sql", "aws"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    # 2/3 = ~66.7%
    assert 60 < result.skill_coverage < 70


def test_analyze_skill_gaps_identifies_missing():
    """Test that missing skills are identified."""
    user_skills = ["python"]
    job_analysis = JobAnalysis(
        required_skills=["python", "sql", "aws"],
        preferred_skills=["docker"],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    missing_skill_names = [gap.skill for gap in result.missing_critical]
    assert "sql" in missing_skill_names or "aws" in missing_skill_names


def test_analyze_skill_gaps_perfect_match():
    """Test analysis when user has all required skills."""
    user_skills = ["python", "sql", "aws"]
    job_analysis = JobAnalysis(
        required_skills=["python", "sql", "aws"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    assert result.skill_coverage == 100.0
    assert len(result.missing_critical) == 0


def test_analyze_skill_gaps_provides_learning_path():
    """Test that learning path is generated."""
    user_skills = ["python"]
    job_analysis = JobAnalysis(
        required_skills=["python", "aws", "docker"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    assert len(result.learning_path) > 0
    assert "estimated_hours" in result.learning_path[0]


def test_analyze_skill_gaps_estimates_preparation_time():
    """Test that preparation time is estimated."""
    user_skills = []
    job_analysis = JobAnalysis(
        required_skills=["python", "aws", "docker", "kubernetes", "sql"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    assert result.estimated_preparation_time != ""
    assert any(unit in result.estimated_preparation_time.lower() for unit in ["week", "month"])


def test_analyze_skill_gaps_recommendation_based_on_coverage():
    """Test that recommendation changes based on coverage."""
    # Strong match
    strong = analyze_skill_gaps(
        ["python", "sql", "aws"],
        JobAnalysis(["python", "sql", "aws"], [], "", "backend", [], [], [], [], [], [], [])
    )
    assert "strong" in strong.recommendation.lower() or "good" in strong.recommendation.lower()

    # Weak match
    weak = analyze_skill_gaps(
        ["python"],
        JobAnalysis(["python", "sql", "aws", "docker", "kubernetes"], [], "", "backend", [], [], [], [], [], [], [])
    )
    assert any(word in weak.recommendation.lower() for word in ["gap", "significant", "substantial"])


def test_skill_gap_includes_resources():
    """Test that skill gaps include learning resources."""
    user_skills = ["python"]
    job_analysis = JobAnalysis(
        required_skills=["python", "aws"],
        preferred_skills=[],
        experience_level="",
        role_category="backend",
    )

    result = analyze_skill_gaps(user_skills, job_analysis)

    if result.missing_critical:
        gap = result.missing_critical[0]
        assert len(gap.resources) > 0
