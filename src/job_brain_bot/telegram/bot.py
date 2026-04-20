from collections.abc import Callable

import structlog
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

from job_brain_bot.ai_intelligence.analyzer import analyze_job_description
from job_brain_bot.ai_intelligence.networking import (
    generate_cold_message,
    generate_referral_request,
)
from job_brain_bot.ai_intelligence.skill_gap import analyze_skill_gaps
from job_brain_bot.config import Settings
from job_brain_bot.db import repo
from job_brain_bot.db.models import Job
from job_brain_bot.db.session import session_scope
from job_brain_bot.health import format_health_status, perform_health_check
from job_brain_bot.networking.http_client import SharedHttpClientLifecycle
from job_brain_bot.resume.parser import parse_resume_content
from job_brain_bot.scraping.time_parser import normalize_time_range
from job_brain_bot.services import fetch_and_rank_jobs_for_user_async
from job_brain_bot.telegram.formatters import (
    format_job_analysis,
    format_job_message,
    format_networking_message,
    format_skill_gap,
)
from job_brain_bot.types import UserProfile


def _parse_profile_args(args: list[str]) -> tuple[str, str, str, list[str]] | None:
    joined = " ".join(args).strip()
    if not joined:
        return None
    parts = [part.strip() for part in joined.split("|")]
    if len(parts) < 3:
        return None
    role, experience, location = parts[0], parts[1], parts[2]
    skills = []
    if len(parts) > 3:
        skills = [skill.strip() for skill in parts[3].split(",") if skill.strip()]
    return role, experience, location, skills


def _parse_time_arg(args: list[str]) -> str:
    """Extract time= parameter from command arguments. Defaults to '7d'."""
    for arg in args:
        if arg.lower().startswith("time="):
            return arg.split("=", 1)[1].strip()
    return "7d"  # Default to 7 days


def _sanitize_free_text(value: str, max_len: int = 80) -> str:
    safe = "".join(ch for ch in value if ch.isalnum() or ch in {" ", "-", "_", "."}).strip()
    return safe[:max_len] or "Contact"


def build_bot_application(
    settings: Settings,
    session_factory: sessionmaker[Session],
    http_client_lifecycle: SharedHttpClientLifecycle,
    scheduler_factory: Callable[[Application], object] | None = None,
) -> Application:
    logger = structlog.get_logger(__name__)
    scheduler_holder: dict[str, object | None] = {"scheduler": None}

    async def _post_init(app: Application) -> None:
        await http_client_lifecycle.startup()
        if scheduler_factory:
            scheduler = scheduler_factory(app)
            scheduler.start()
            scheduler_holder["scheduler"] = scheduler
            logger.info("scheduler_started")

    async def _post_shutdown(_: Application) -> None:
        scheduler = scheduler_holder.get("scheduler")
        if scheduler:
            try:
                scheduler.shutdown(wait=False)
            except Exception:
                logger.exception("scheduler_shutdown_failed")
        await http_client_lifecycle.shutdown()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    def _session() -> Callable:
        return session_scope(session_factory)

    async def _safe_reply(
        update: Update, text: str, *, disable_web_page_preview: bool = False
    ) -> None:
        if not update.message:
            return
        try:
            await update.message.reply_text(text, disable_web_page_preview=disable_web_page_preview)
        except TelegramError:
            logger.exception("telegram_reply_failed")

    def _resolve_user_job(session: Session, user_id: int, args: list[str]) -> Job | None:
        views = repo.list_user_job_views(session, user_id, limit=20)
        if not views:
            return None
        job_index = 0
        if args:
            try:
                job_index = int(args[0]) - 1
            except ValueError:
                job_index = 0
        if job_index < 0 or job_index >= len(views):
            return None
        return repo.get_job(session, views[job_index].job_id)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        profile = UserProfile(
            user_id=update.effective_user.id,
            role="",
            experience="",
            location="",
            skills=[],
            resume_text="",
            alerts_enabled=False,
        )
        with _session() as session:
            repo.upsert_user(session, profile)
        await _safe_reply(
            update,
            "🧠 Welcome to Job Brain Bot with AI Intelligence!\n\n"
            "*Getting Started:*\n"
            "• /setprofile role|experience|location|skills - Configure your profile\n"
            "• /resume - Upload your resume for better matching\n"
            "• /jobs [time=24h/48h/7d] - Find jobs with time filtering\n\n"
            "*🤖 AI Features:*\n"
            "🤖 /analyze [job_number] - AI analysis of job requirements\n"
            "📊 /skills [job_number] - Skill gap analysis & learning paths\n"
            "💬 /network [job_number] [name] - Generate cold outreach messages\n"
            "🎯 /referral [job_number] [name] - Generate referral requests\n\n"
            "*System Commands:*\n"
            "💓 /health - Check bot health & database connectivity\n"
            "*Other Commands:*\n"
            "• /recommend - Get top job recommendations\n"
            "• /alerts on/off - Enable/disable job alerts",
        )

    async def setprofile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        parsed = _parse_profile_args(context.args)
        if not parsed:
            await _safe_reply(
                update,
                "Usage: /setprofile Cybersecurity Analyst|Fresher|Hyderabad|Python,SIEM,Network Security",
            )
            return
        role, experience, location, skills = parsed
        with _session() as session:
            existing = repo.get_user(session, update.effective_user.id)
            alerts_enabled = existing.alerts_enabled if existing else False
            repo.upsert_user(
                session,
                UserProfile(
                    user_id=update.effective_user.id,
                    role=role,
                    experience=experience,
                    location=location,
                    skills=skills,
                    resume_text=existing.resume_text if existing else "",
                    alerts_enabled=alerts_enabled,
                ),
            )
        await _safe_reply(update, "Profile saved successfully.")

    async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return

        time_range = _parse_time_arg(context.args or [])
        time_range = normalize_time_range(time_range)

        with _session() as session:
            user = repo.get_user(session, update.effective_user.id)
            if not user:
                await _safe_reply(
                    update,
                    "Please set up your profile first with /setprofile.\n"
                    "Usage: /setprofile role|experience|location|skills",
                )
                return

            ranked = await fetch_and_rank_jobs_for_user_async(
                session,
                settings,
                http_client_lifecycle.client,
                update.effective_user.id,
                max_results=5,
                time_range=time_range,
            )

        if not ranked:
            time_display = {"24h": "24 hours", "48h": "48 hours", "7d": "7 days"}.get(
                time_range, time_range
            )
            await _safe_reply(
                update,
                f"No jobs found in the last {time_display}.\n"
                f"Try expanding your search with: /jobs time=7d\n"
                "Or update your profile with /setprofile",
            )
            return

        time_display = {"24h": "24 hours", "48h": "48 hours", "7d": "7 days"}.get(
            time_range, time_range
        )
        with _session() as session:
            repo.replace_user_job_views(
                session, update.effective_user.id, [item.job.job_id for item in ranked]
            )
        await _safe_reply(
            update, f"🎯 Here are your top personalized job matches (last {time_display}):"
        )
        for idx, item in enumerate(ranked, start=1):
            rendered = format_job_message(item)
            await _safe_reply(update, f"#{idx}\n{rendered}", disable_web_page_preview=True)

    async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        state = "on"
        if context.args:
            state = context.args[0].lower()
        enable = state in {"on", "enable", "true", "1"}

        with _session() as session:
            existing = repo.get_user(session, update.effective_user.id)
            if not existing:
                await _safe_reply(
                    update, "Please run /start and /setprofile before configuring alerts."
                )
                return
            profile = UserProfile(
                user_id=existing.user_id,
                role=existing.role,
                experience=existing.experience,
                location=existing.location,
                skills=[x.strip() for x in existing.skills.split(",") if x.strip()],
                resume_text=existing.resume_text,
                alerts_enabled=enable,
            )
            repo.upsert_user(session, profile)
        await _safe_reply(update, f"Daily alerts {'enabled' if enable else 'disabled'}.")

    async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        with _session() as session:
            ranked = await fetch_and_rank_jobs_for_user_async(
                session,
                settings,
                http_client_lifecycle.client,
                update.effective_user.id,
                max_results=3,
            )
        if not ranked:
            await _safe_reply(
                update, "No recommendations available. Set profile with /setprofile first."
            )
            return
        with _session() as session:
            repo.replace_user_job_views(
                session, update.effective_user.id, [item.job.job_id for item in ranked]
            )
        await _safe_reply(update, "🚀 Top recommendations picked for your profile:")
        for idx, item in enumerate(ranked, start=1):
            rendered = format_job_message(item)
            await _safe_reply(update, f"#{idx}\n{rendered}", disable_web_page_preview=True)

    async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        if not update.message.document:
            await _safe_reply(
                update, "Upload your resume as a text-based document with caption /resume."
            )
            return
        telegram_file = await context.bot.get_file(update.message.document.file_id)
        raw = await telegram_file.download_as_bytearray()
        filename = update.message.document.file_name or "resume.txt"
        role_for_ontology = ""
        with _session() as session:
            existing = repo.get_user(session, update.effective_user.id)
            if not existing:
                await update.message.reply_text(
                    "Please run /start and /setprofile before uploading a resume."
                )
                return
            role_for_ontology = existing.role

        parsed_resume = parse_resume_content(filename, bytes(raw), target_role=role_for_ontology)
        if not parsed_resume.text:
            await _safe_reply(
                update, "Could not parse resume text. Please upload PDF, DOCX, or UTF-8 text."
            )
            return

        with _session() as session:
            existing = repo.get_user(session, update.effective_user.id)
            if not existing:
                return
            merged_skills = set(x.strip() for x in existing.skills.split(",") if x.strip())
            merged_skills.update(parsed_resume.skills)
            effective_experience = existing.experience or parsed_resume.inferred_experience
            resume_payload = (
                f"{parsed_resume.text}\n\n"
                f"EXTRACTED_SKILLS: {', '.join(parsed_resume.skills)}\n"
                f"EXTRACTED_EXPERIENCE: {parsed_resume.inferred_experience}\n"
                f"EXTRACTED_KEYWORDS: {', '.join(parsed_resume.keywords)}"
            )[:24000]
            profile = UserProfile(
                user_id=existing.user_id,
                role=existing.role,
                experience=effective_experience,
                location=existing.location,
                skills=sorted(merged_skills),
                resume_text=resume_payload,
                alerts_enabled=existing.alerts_enabled,
            )
            repo.upsert_user(session, profile)
        await _safe_reply(
            update,
            "Resume uploaded and parsed.\n"
            f"Detected skills: {', '.join(parsed_resume.skills[:8]) or 'none'}\n"
            f"Detected experience: {parsed_resume.inferred_experience or 'not found'}",
        )

    async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Analyze a job posting using AI."""
        if not update.effective_user or not update.message:
            return

        with _session() as session:
            user = repo.get_user(session, update.effective_user.id)
            if not user:
                await _safe_reply(update, "Please set your profile first with /setprofile")
                return
            job = _resolve_user_job(session, update.effective_user.id, context.args)
            if not job:
                await _safe_reply(update, "Run /jobs first, then use /analyze [job_number].")
                return

        if not settings.ai_analysis_enabled:
            await _safe_reply(update, "AI analysis is currently disabled.")
            return

        # Analyze the job
        analysis = analyze_job_description(job.title, job.description)

        await _safe_reply(
            update,
            f"🤖 AI Analysis for: {job.title}\n\n{format_job_analysis(analysis)}",
            disable_web_page_preview=True,
        )

    async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Analyze skill gaps for your profile vs jobs or a specific job."""
        if not update.effective_user or not update.message:
            return

        with _session() as session:
            user = repo.get_user(session, update.effective_user.id)
            if not user:
                await _safe_reply(update, "Please set your profile first with /setprofile")
                return

            user_skills = [s.strip() for s in user.skills.split(",") if s.strip()]

            selected = _resolve_user_job(session, update.effective_user.id, context.args)
            if selected:
                analysis = analyze_job_description(selected.title, selected.description)
                gap = analyze_skill_gaps(user_skills, analysis)
                await _safe_reply(
                    update,
                    f"📊 Skill Gap Analysis: Your Profile vs {selected.title}\n\n{format_skill_gap(gap)}",
                    disable_web_page_preview=True,
                )
                return

            jobs = []
            for view in repo.list_user_job_views(session, update.effective_user.id, limit=20):
                found = repo.get_job(session, view.job_id)
                if found:
                    jobs.append(found)
            if not jobs:
                await _safe_reply(update, "Run /jobs first, then use /skills [job_number].")
                return

            from job_brain_bot.matching.scoring import rank_jobs_for_user

            ranked = rank_jobs_for_user(user, jobs)

            if ranked:
                best_job = ranked[0].job
                analysis = analyze_job_description(best_job.title, best_job.description)
                gap = analyze_skill_gaps(user_skills, analysis)

                await _safe_reply(
                    update,
                    f"📊 Skill Gap Analysis: Your Profile vs Top Job Match\n"
                    f"Job: {best_job.title} at {best_job.company}\n\n{format_skill_gap(gap)}",
                    disable_web_page_preview=True,
                )
            else:
                await _safe_reply(update, "Could not analyze skills. Please try again later.")

    async def network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate networking messages. Usage: /network [job_index] [contact_name]"""
        if not update.effective_user or not update.message:
            return

        with _session() as session:
            user = repo.get_user(session, update.effective_user.id)
            if not user:
                await _safe_reply(update, "Please set your profile first with /setprofile")
                return

            user_skills = [s.strip() for s in user.skills.split(",") if s.strip()]

            # Parse arguments
            job_index = 0
            contact_name = "Hiring Manager"

            if len(context.args) >= 1:
                try:
                    job_index = int(context.args[0]) - 1
                except ValueError:
                    contact_name = _sanitize_free_text(context.args[0])

            if len(context.args) >= 2:
                contact_name = _sanitize_free_text(context.args[1])

            selected = _resolve_user_job(session, update.effective_user.id, [str(job_index + 1)])
            if not selected:
                await _safe_reply(update, "Run /jobs first, then use /network [job_number] [name].")
                return

            job = selected

            if not settings.networking_generator_enabled:
                await _safe_reply(update, "Networking generator is currently disabled.")
                return

            # Generate cold message
            message = generate_cold_message(
                target_name=contact_name,
                target_title="Hiring Manager",
                company=job.company,
                job_title=job.title,
                user_name=user.role or "Candidate",  # Use role as name placeholder
                user_role=user.role,
                user_skills=user_skills,
                message_type="linkedin_connection",
            )

            await _safe_reply(
                update,
                f"💬 Networking Message for {job.title} at {job.company}\n\n{format_networking_message(message)}",
                disable_web_page_preview=True,
            )

    async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate referral request message. Usage: /referral [job_index] [contact_name]"""
        if not update.effective_user or not update.message:
            return

        with _session() as session:
            user = repo.get_user(session, update.effective_user.id)
            if not user:
                await _safe_reply(update, "Please set your profile first with /setprofile")
                return

            user_skills = [s.strip() for s in user.skills.split(",") if s.strip()]

            # Parse arguments
            job_index = 0
            contact_name = "Contact"

            if len(context.args) >= 1:
                try:
                    job_index = int(context.args[0]) - 1
                except ValueError:
                    contact_name = _sanitize_free_text(context.args[0])

            if len(context.args) >= 2:
                contact_name = _sanitize_free_text(context.args[1])

            selected = _resolve_user_job(session, update.effective_user.id, [str(job_index + 1)])
            if not selected:
                await _safe_reply(
                    update, "Run /jobs first, then use /referral [job_number] [name]."
                )
                return

            job = selected

            if not settings.networking_generator_enabled:
                await _safe_reply(update, "Networking generator is currently disabled.")
                return

            # Generate referral request
            message = generate_referral_request(
                contact_name=contact_name,
                company=job.company,
                job_title=job.title,
                user_name=user.role or "Candidate",
                user_role=user.role,
                user_skills=user_skills,
                request_type="colleague",
            )

            await _safe_reply(
                update,
                f"🎯 Referral Request for {job.title} at {job.company}\n\n{format_networking_message(message)}",
                disable_web_page_preview=True,
            )

    async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check bot health status and database connectivity."""
        if not update.effective_user or not update.message:
            return

        admin_ids = settings.admin_ids_set()
        if admin_ids and update.effective_user.id not in admin_ids:
            await _safe_reply(update, "Health diagnostics are restricted to bot administrators.")
            return

        # Perform health check
        status = perform_health_check(settings)
        formatted = format_health_status(status)

        await _safe_reply(update, formatted)

    async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        error_text = str(context.error or "")
        logger.exception("telegram_handler_error", error=error_text)
        if isinstance(update, Update) and update.message:
            try:
                lowered = error_text.lower()
                if isinstance(context.error, OperationalError) or (
                    "failed to resolve host" in lowered
                    or "name or service not known" in lowered
                    or "could not translate host name" in lowered
                    or "connection refused" in lowered
                ):
                    await update.message.reply_text(
                        "Database is temporarily unavailable. Please try again in a minute."
                    )
                    return
                await update.message.reply_text(
                    "Something went wrong while processing your request. Please try again."
                )
            except TelegramError:
                logger.exception("telegram_error_reply_failed")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setprofile", setprofile))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("recommend", recommend))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("skills", skills))
    app.add_handler(CommandHandler("network", network))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("health", health))
    app.add_error_handler(_error_handler)
    return app
