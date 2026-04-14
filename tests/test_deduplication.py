from job_brain_bot.scraping.collector import dedupe_jobs
from job_brain_bot.types import JobRecord


def test_dedupe_prefers_richer_job_record() -> None:
    first = JobRecord(
        title="Cybersecurity Analyst",
        company="Acme",
        location="Hyderabad",
        experience="0-2 years",
        link="https://example.com/job/1?utm_source=x",
        source="company_page",
        description="short",
    )
    second = JobRecord(
        title="Cybersecurity Analyst",
        company="Acme",
        location="Hyderabad",
        experience="0-2 years",
        link="https://example.com/job/2",
        source="company_page",
        description="This is a much richer and longer job description.",
    )
    deduped = dedupe_jobs([first, second])
    assert len(deduped) == 1
    assert deduped[0].description.startswith("This is a much richer")
