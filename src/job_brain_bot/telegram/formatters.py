from urllib.parse import quote_plus

from job_brain_bot.ai_intelligence.analyzer import JobAnalysis
from job_brain_bot.ai_intelligence.networking import NetworkingMessage
from job_brain_bot.ai_intelligence.skill_gap import GapAnalysis
from job_brain_bot.db.models import Job
from job_brain_bot.matching.scoring import ScoredJob
from job_brain_bot.scraping.time_parser import format_time_ago


def format_job_analysis(analysis: JobAnalysis) -> str:
    """Format job analysis for Telegram display."""
    lines = [
        f"📋 *Role Category:* {analysis.role_category.title()}",
        f"🎯 *Experience Level:* {analysis.experience_level.title()}",
        "",
        "*🔧 Required Skills:*",
    ]

    if analysis.required_skills:
        lines.append(", ".join(analysis.required_skills[:10]))
    else:
        lines.append("None identified")

    if analysis.preferred_skills:
        lines.extend(["", "*⭐ Preferred Skills:*", ", ".join(analysis.preferred_skills[:8])])

    if analysis.certifications_mentioned:
        lines.extend(["", "*📜 Certifications Mentioned:*", ", ".join(analysis.certifications_mentioned)])

    if analysis.soft_skills:
        lines.extend(["", "*🤝 Soft Skills:*", ", ".join(analysis.soft_skills[:6])])

    if analysis.key_responsibilities:
        lines.extend(["", "*📝 Key Responsibilities:*"])
        for i, resp in enumerate(analysis.key_responsibilities[:5], 1):
            lines.append(f"{i}. {resp[:80]}..." if len(resp) > 80 else f"{i}. {resp}")

    if analysis.red_flags:
        lines.extend(["", "⚠️ *Potential Concerns:*", analysis.red_flags[0][:100]])

    return "\n".join(lines)


def format_skill_gap(gap: GapAnalysis) -> str:
    """Format skill gap analysis for Telegram display."""
    lines = [
        gap.recommendation,
        "",
        f"*📊 Skill Coverage:* {gap.skill_coverage}%",
        f"*⏱ Estimated Prep Time:* {gap.estimated_preparation_time}",
        "",
        f"*✅ You Have ({len(gap.matched_skills)}):*",
    ]

    if gap.matched_skills:
        lines.append(", ".join(gap.matched_skills[:10]))
    else:
        lines.append("None yet - focus on building foundational skills")

    if gap.missing_critical:
        lines.extend(["", f"*📚 Skills to Learn ({len(gap.missing_critical)}):*"])
        for skill_gap in gap.missing_critical[:6]:
            priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                skill_gap.priority, "⚪"
            )
            lines.append(f"{priority_emoji} *{skill_gap.skill}* ({skill_gap.priority}, ~{skill_gap.learning_hours}h)")
            if skill_gap.resources:
                lines.append(f"   📖 {skill_gap.resources[0]}")

    if gap.certifications_to_consider:
        lines.extend(["", "*🎓 Certifications to Consider:*"])
        for cert in gap.certifications_to_consider[:3]:
            level = cert.get("level", "")
            cost = cert.get("cost", "")
            lines.append(f"• {cert['name']} ({level}, {cost})")

    if gap.learning_path:
        lines.extend(["", "*🎯 Suggested Learning Order:*"])
        for i, path in enumerate(gap.learning_path[:4], 1):
            lines.append(f"{i}. {path['skill']} (~{path['estimated_hours']}h)")

    return "\n".join(lines)


def format_networking_message(message: NetworkingMessage) -> str:
    """Format networking message for Telegram display."""
    lines = [
        f"*Subject:* {message.subject}",
        "",
        "*Message:*",
        "```",
        message.body[:2000],  # Limit length for Telegram
        "```",
        "",
        "*💡 Tips:*",
    ]

    for tip in message.tips:
        lines.append(f"• {tip}")

    lines.extend([
        "",
        "*🔄 Follow-up (if no response after 5-7 days):*",
        "```",
        message.follow_up[:500],
        "```",
    ])

    return "\n".join(lines)


def recruiter_search_query(company: str, role: str) -> str:
    return f"{company} recruiter {role}"


def recruiter_search_url(company: str, role: str) -> str:
    query = quote_plus(f"{company} HR recruiter LinkedIn {role}")
    return f"https://www.google.com/search?q={query}"


def format_job_message(scored_job: ScoredJob) -> str:
    job: Job = scored_job.job
    link = job.link or "N/A"
    query = recruiter_search_query(job.company, job.title)
    score_badge = "🔥 Strong Match" if scored_job.total_score >= 75 else "✅ Good Match" if scored_job.total_score >= 55 else "🟡 Explore"

    # Format posting time
    posted_time = format_time_ago(job.posted_date)

    lines = [
        f"🔹 {job.title} - {job.company}",
        f"{score_badge}",
        f"📍 {job.location}",
        f"💼 {job.experience}",
        f"⏱ Posted: {posted_time}",
        f"🔗 Apply Link: {link}",
        f"⭐ Match Score: {scored_job.total_score}/100",
        f"🧠 Score Breakdown: Skills {scored_job.skills_score:.1f}, Exp {scored_job.experience_score:.1f}, Location {scored_job.location_score:.1f}, Recency {scored_job.recency_score:.1f}",
        "🔍 Suggested LinkedIn Search:",
        f"\"{query}\"",
        f"Search Link: {recruiter_search_url(job.company, job.title)}",
    ]
    insight = (job.signals_json or {}).get("insight", "")
    if insight:
        lines.append(f"📈 Insight: {insight}")
    return "\n".join(lines)
