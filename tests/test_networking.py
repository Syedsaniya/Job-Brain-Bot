"""Tests for networking message generator module."""

from job_brain_bot.ai_intelligence.networking import (
    NetworkingMessage,
    generate_cold_message,
    generate_linkedin_invite_note,
    generate_referral_request,
)


def test_generate_cold_message_returns_structure():
    """Test that cold message generation returns proper structure."""
    result = generate_cold_message(
        target_name="John Smith",
        target_title="Engineering Manager",
        company="TechCorp",
        job_title="Software Engineer",
        user_name="Jane Doe",
        user_role="Developer",
        user_skills=["Python", "JavaScript", "React"],
    )

    assert isinstance(result, NetworkingMessage)
    assert result.subject != ""
    assert result.body != ""
    assert len(result.tips) > 0
    assert result.follow_up != ""


def test_generate_cold_message_includes_user_skills():
    """Test that generated message mentions user skills."""
    result = generate_cold_message(
        target_name="John",
        target_title="Manager",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python", "AWS"],
    )

    # Check that skills appear in body or subject
    body_lower = result.body.lower()
    assert "python" in body_lower or "aws" in body_lower


def test_generate_cold_message_includes_company():
    """Test that generated message mentions company."""
    result = generate_cold_message(
        target_name="John",
        target_title="Manager",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    assert "techcorp" in result.body.lower() or "TechCorp" in result.body


def test_generate_cold_message_includes_job_title():
    """Test that generated message mentions job title."""
    result = generate_cold_message(
        target_name="John",
        target_title="Manager",
        company="TechCorp",
        job_title="Senior Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    body_lower = result.body.lower()
    assert "engineer" in body_lower or "senior" in body_lower


def test_generate_cold_message_different_types():
    """Test different message types."""
    types = ["linkedin_connection", "email_hiring_manager", "industry_professional"]

    for msg_type in types:
        result = generate_cold_message(
            target_name="John",
            target_title="Manager",
            company="TechCorp",
            job_title="Engineer",
            user_name="Jane",
            user_role="Developer",
            user_skills=["Python"],
            message_type=msg_type,
        )

        assert isinstance(result, NetworkingMessage)
        assert len(result.body) > 50


def test_generate_referral_request_returns_structure():
    """Test that referral request returns proper structure."""
    result = generate_referral_request(
        contact_name="John Doe",
        company="TechCorp",
        job_title="Software Engineer",
        user_name="Jane Smith",
        user_role="Developer",
        user_skills=["Python", "React"],
    )

    assert isinstance(result, NetworkingMessage)
    assert result.subject != ""
    assert result.body != ""
    assert len(result.tips) > 0


def test_generate_referral_request_polite_tone():
    """Test that referral request has polite tone."""
    result = generate_referral_request(
        contact_name="John",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    # Should contain polite language
    body_lower = result.body.lower()
    polite_words = ["would", "could", "please", "thank", "appreciate"]
    assert any(word in body_lower for word in polite_words)


def test_generate_referral_request_alumni():
    """Test alumni referral request."""
    result = generate_referral_request(
        contact_name="John",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
        request_type="alumni",
        school="MIT",
    )

    assert isinstance(result, NetworkingMessage)
    # Should mention school
    body_lower = result.body.lower()
    assert "mit" in body_lower or "alumn" in body_lower


def test_generate_referral_request_mutual_connection():
    """Test mutual connection referral request."""
    result = generate_referral_request(
        contact_name="John",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
        request_type="mutual_connection",
        mutual_contact="Bob Smith",
    )

    assert isinstance(result, NetworkingMessage)
    # Should mention mutual connection
    assert "bob smith" in result.body.lower() or "bob" in result.body.lower()


def test_generate_linkedin_invite_note_short():
    """Test LinkedIn invite note is short enough."""
    note = generate_linkedin_invite_note(
        target_name="John Smith",
        company="TechCorp",
        job_title="Engineer",
        user_role="Developer",
        user_skills=["Python", "React"],
    )

    # LinkedIn limit is 300 characters
    assert len(note) <= 300
    assert len(note) > 20  # Should have some content


def test_generate_linkedin_invite_note_includes_key_info():
    """Test LinkedIn note includes key information."""
    note = generate_linkedin_invite_note(
        target_name="John",
        company="TechCorp",
        job_title="Senior Engineer",
        user_role="Developer",
        user_skills=["Python"],
    )

    note_lower = note.lower()
    # Should mention role or skills
    assert any(word in note_lower for word in ["developer", "python", "engineer", "techcorp"])


def test_cold_message_tips_are_helpful():
    """Test that tips are actually helpful."""
    result = generate_cold_message(
        target_name="John",
        target_title="Manager",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    # Tips should contain actionable advice
    tips_text = " ".join(result.tips).lower()
    helpful_keywords = ["personalize", "profile", "follow", "research", "connect"]
    assert any(keyword in tips_text for keyword in helpful_keywords)


def test_follow_up_message_different_from_initial():
    """Test that follow-up is different from initial message."""
    result = generate_cold_message(
        target_name="John",
        target_title="Manager",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    # Follow-up should be different from main body
    assert result.follow_up != result.body
    # Follow-up should be shorter
    assert len(result.follow_up) < len(result.body)


def test_referral_request_includes_easy_out():
    """Test that referral request includes easy way to decline."""
    result = generate_referral_request(
        contact_name="John",
        company="TechCorp",
        job_title="Engineer",
        user_name="Jane",
        user_role="Developer",
        user_skills=["Python"],
    )

    # Should have polite, non-pushy tone
    tips_text = " ".join(result.tips).lower()
    assert any(phrase in tips_text for phrase in ["easy", "out", "comfortable", "pressure"])
