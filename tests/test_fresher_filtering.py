from job_brain_bot.db.models import Job
from job_brain_bot.matching.filters import filter_jobs_for_profile, is_fresher_profile


def test_fresher_profile_detection() -> None:
    assert is_fresher_profile("Fresher")
    assert is_fresher_profile("0-2 years")
    assert not is_fresher_profile("4-6 years")


def test_fresher_filter_removes_senior_roles() -> None:
    jobs = [
        Job(
            title="Junior Data Analyst",
            company="Acme",
            location="Remote",
            experience="0-2 years",
            link="https://acme.jobs/1",
            source="company_page",
            description="entry level role for graduate candidates",
        ),
        Job(
            title="Senior Data Analyst",
            company="Beta",
            location="Remote",
            experience="4-6 years",
            link="https://beta.jobs/2",
            source="company_page",
            description="senior level role",
        ),
    ]
    filtered = filter_jobs_for_profile(jobs, "Fresher")
    assert len(filtered) == 1
    assert filtered[0].title == "Junior Data Analyst"
