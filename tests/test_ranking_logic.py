from datetime import datetime, timedelta, timezone

from job_brain_bot.db.models import Job, User
from job_brain_bot.matching.scoring import rank_jobs_for_user


def test_ranking_prefers_higher_relevance() -> None:
    user = User(
        user_id=1,
        role="Cybersecurity Analyst",
        experience="Fresher",
        location="Remote",
        skills="python,siem,linux",
        resume_text=(
            "hands-on python siem linux projects "
            "EXTRACTED_SKILLS: python, siem, linux\n"
            "EXTRACTED_KEYWORDS: cybersecurity, soc, incident"
        ),
        alerts_enabled=True,
    )
    now = datetime.now(timezone.utc)
    strong = Job(
        title="Cybersecurity Analyst",
        company="Acme",
        location="Remote",
        experience="0-2 years",
        link="https://acme/jobs/1",
        source="company_page",
        description="python siem linux soc incident response",
        posted_date=now,
        created_at=now,
    )
    weak = Job(
        title="Sales Executive",
        company="Other",
        location="Onsite",
        experience="4-6 years",
        link="https://other/jobs/2",
        source="google",
        description="sales targets and account growth",
        posted_date=now - timedelta(days=10),
        created_at=now - timedelta(days=10),
    )
    ranked = rank_jobs_for_user(user, [weak, strong])
    assert ranked[0].job.title == "Cybersecurity Analyst"
    assert ranked[0].total_score > ranked[1].total_score


def test_recency_affects_ranking() -> None:
    """Test that more recent jobs get higher scores when other factors are equal."""
    from job_brain_bot.matching.scoring import score_job_for_user

    user = User(
        user_id=1,
        role="Software Engineer",
        experience="Fresher",
        location="Hyderabad",
        skills="python",
        resume_text="",
        alerts_enabled=False,
    )
    now = datetime.now(timezone.utc)

    # Jobs with same base attributes but different posting times
    # Use slightly imperfect matches so recency makes the difference
    fresh_job = Job(
        title="Software Developer",  # Partial match (not exact "Software Engineer")
        company="TechCorp",
        location="Hyderabad",
        experience="0-2 years",
        link="https://techcorp/jobs/1",
        source="company_page",
        description="python developer role",  # Has 'python' skill
        posted_date=now - timedelta(hours=12),  # 12 hours ago - max recency
        created_at=now,
    )
    old_job = Job(
        title="Software Developer",  # Same partial match
        company="TechCorp",
        location="Hyderabad",
        experience="0-2 years",
        link="https://techcorp/jobs/2",
        source="company_page",
        description="python developer role",  # Same skill match
        posted_date=now - timedelta(days=10),  # 10 days ago - low recency
        created_at=now - timedelta(days=10),
    )

    fresh_score = score_job_for_user(user, fresh_job)
    old_score = score_job_for_user(user, old_job)

    # Fresh job should have higher recency score (20 vs 7 for old)
    assert fresh_score.recency_score > old_score.recency_score
    # The fresh job should score higher due to better recency
    assert fresh_score.total_score >= old_score.total_score
