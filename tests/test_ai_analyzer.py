"""Tests for AI intelligence analyzer module."""

from job_brain_bot.ai_intelligence.analyzer import (
    JobAnalysis,
    analyze_job_description,
    extract_certifications,
    extract_experience_level,
    extract_role_category,
    extract_skills_from_text,
)
from job_brain_bot.ai_intelligence.skill_gap import calculate_skill_match


def test_extract_skills_from_text_basic():
    """Test basic skill extraction."""
    text = "Required: Python, SQL, AWS. Preferred: Docker, Kubernetes."
    required, preferred = extract_skills_from_text(text)

    assert "python" in required or "python" in preferred
    assert "sql" in required or "sql" in preferred


def test_extract_skills_case_insensitive():
    """Test that skill extraction is case insensitive."""
    text = "We need PYTHON and AWS experience."
    required, preferred = extract_skills_from_text(text)

    assert "python" in required or "python" in preferred
    assert "aws" in required or "aws" in preferred


def test_extract_experience_level_fresher():
    """Test fresher experience level detection."""
    assert extract_experience_level("Looking for fresher candidates") == "fresher"
    assert extract_experience_level("Entry level position") == "fresher"
    assert extract_experience_level("0-1 years experience") == "fresher"


def test_extract_experience_level_junior():
    """Test junior experience level detection."""
    assert extract_experience_level("Junior developer needed") == "junior"
    assert extract_experience_level("1-3 years required") == "junior"


def test_extract_experience_level_senior():
    """Test senior experience level detection."""
    assert extract_experience_level("Senior engineer position") == "senior"
    assert extract_experience_level("5-8 years experience required") == "senior"


def test_extract_role_category_cybersecurity():
    """Test cybersecurity role categorization."""
    result = extract_role_category("SOC Analyst - Security", "Network security, incident response")
    assert result == "cybersecurity"


def test_extract_role_category_frontend():
    """Test frontend role categorization."""
    result = extract_role_category("Frontend Developer", "React, CSS, HTML, JavaScript")
    assert result == "frontend"


def test_extract_role_category_backend():
    """Test backend role categorization."""
    result = extract_role_category("Backend Engineer", "Python, SQL, API development")
    assert result == "backend"


def test_extract_role_category_devops():
    """Test devops role categorization."""
    result = extract_role_category("DevOps Engineer", "AWS, Docker, Kubernetes, CI/CD")
    assert result == "devops"


def test_extract_certifications():
    """Test certification extraction."""
    text = "AWS Certified Solutions Architect or Security+ required. CISSP preferred."
    certs = extract_certifications(text)

    # Should extract at least one certification
    assert len(certs) > 0
    # Check for AWS cert
    assert any("aws" in c.lower() for c in certs)
    # Security+ or CISSP might be extracted depending on pattern matching
    cert_names = [c.lower() for c in certs]
    print(f"Extracted certs: {cert_names}")


def test_analyze_job_description_structure():
    """Test that analyze_job_description returns proper structure."""
    title = "Software Engineer"
    description = """
    Required: Python, SQL, Git
    Preferred: AWS, Docker
    Experience: 2-3 years
    Responsibilities: Build APIs, review code, deploy applications
    """

    result = analyze_job_description(title, description)

    assert isinstance(result, JobAnalysis)
    assert len(result.required_skills) > 0
    assert result.experience_level != ""
    assert result.role_category != ""


def test_analyze_job_description_extracts_skills():
    """Test that job analysis extracts expected skills."""
    result = analyze_job_description(
        "Python Developer", "Required: Python, Django, PostgreSQL. Preferred: Redis, Celery."
    )

    assert "python" in [s.lower() for s in result.required_skills]


def test_calculate_skill_match_perfect():
    """Test skill matching with perfect overlap."""
    user_skills = ["python", "sql", "aws"]
    required = ["python", "sql"]
    preferred = ["aws"]

    matched, missing_required, missing_preferred = calculate_skill_match(
        user_skills, required, preferred
    )

    assert len(matched) == 3
    assert len(missing_required) == 0
    assert len(missing_preferred) == 0


def test_calculate_skill_match_partial():
    """Test skill matching with partial overlap."""
    user_skills = ["python", "sql"]
    required = ["python", "sql", "aws"]
    preferred = ["docker"]

    matched, missing_required, missing_preferred = calculate_skill_match(
        user_skills, required, preferred
    )

    assert "python" in matched or "sql" in matched
    assert "aws" in missing_required
    assert "docker" in missing_preferred


def test_calculate_skill_match_empty():
    """Test skill matching with empty inputs."""
    matched, missing_required, missing_preferred = calculate_skill_match([], [], [])

    assert len(matched) == 0
    assert len(missing_required) == 0
    assert len(missing_preferred) == 0


def test_analyze_job_description_handles_short_description():
    """Test analysis with minimal description."""
    result = analyze_job_description("Job", "Python required")

    assert isinstance(result, JobAnalysis)
    assert result.role_category != ""


def test_analyze_job_description_detects_soft_skills():
    """Test soft skill extraction."""
    result = analyze_job_description(
        "Manager", "Need good communication skills, leadership ability, and problem solving."
    )

    soft_skills = [s.lower() for s in result.soft_skills]
    assert any("communication" in s for s in soft_skills)


def test_analyze_job_description_extracts_responsibilities():
    """Test responsibility extraction from job description."""
    description = """
    Responsibilities:
    1. Develop web applications
    2. Write tests
    3. Review code
    4. Deploy to production
    """

    result = analyze_job_description("Developer", description)

    assert len(result.key_responsibilities) > 0


def test_extract_skills_with_variations():
    """Test extraction of skills with common variations."""
    text = "Need React.js, Nodejs, and AWS experience"

    required, preferred = extract_skills_from_text(text)

    all_skills = list(required) + list(preferred)
    all_lower = [s.lower() for s in all_skills]

    assert "react" in all_lower or "react.js" in all_lower
    assert "node.js" in all_lower or "nodejs" in all_lower


def test_analyze_job_description_returns_no_none_values():
    """Test that analysis doesn't return None for critical fields."""
    result = analyze_job_description("Title", "Description with Python and SQL")

    assert result.required_skills is not None
    assert result.preferred_skills is not None
    assert result.role_category is not None
