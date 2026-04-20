"""Networking message generator.

Creates personalized cold outreach messages and referral requests
based on user profile and target job/company.
"""

import random
from dataclasses import dataclass

from job_brain_bot.ai_intelligence.analyzer import JobAnalysis


@dataclass(slots=True)
class NetworkingMessage:
    """Generated networking message with metadata."""

    subject: str
    body: str
    tips: list[str]
    follow_up: str


# Message templates for different scenarios
COLD_MESSAGE_TEMPLATES = {
    "linkedin_connection": [
        """Hi {name},

I came across your profile while researching {company} and was impressed by your experience in {topic}.

I'm a {user_role} with experience in {user_skills}. I'm very interested in the {job_title} role at {company} and would love to learn more about the team and culture.

Would you be open to a brief chat? I'd really appreciate any insights you could share.

Best regards,
{user_name}""",
        """Hi {name},

I noticed you're working at {company} in {topic}. I'm currently exploring opportunities in this space and the {job_title} position caught my attention.

With my background in {user_skills}, I believe I could bring value to your team. I'd love to connect and learn about your experience at {company}.

Would you have 15 minutes for a quick conversation?

Thanks,
{user_name}""",
    ],
    "email_hiring_manager": [
        """Subject: Interested in {job_title} - {user_role} with {top_skill} expertise

Hi {name},

I hope this email finds you well. I'm writing to express my strong interest in the {job_title} position at {company}.

Having worked with {user_skills}, I've developed expertise that aligns well with your requirements, particularly in {matching_skill}. I'm particularly drawn to {company} because {company_interest_reason}.

I've attached my resume and would welcome the opportunity to discuss how I can contribute to your team.

Thank you for your time and consideration.

Best regards,
{user_name}
{contact_info}""",
    ],
    "industry_professional": [
        """Hi {name},

I'm {user_name}, a {user_role} passionate about {topic}. I've been following {company}'s work in this area and am really impressed by {specific_achievement}.

I'm reaching out because I'm considering the {job_title} role and would value your perspective as someone with deep experience in the field. I'd love to hear about your journey and any advice you might have.

Would you be open to connecting?

Best,
{user_name}""",
    ],
}

REFERRAL_TEMPLATES = {
    "colleague": [
        """Hi {name},

I hope you're doing well! I noticed you're working at {company} and wanted to reach out.

I'm very interested in the {job_title} position that recently opened up. Given my experience with {user_skills}, I think I'd be a strong fit for the team.

Would you feel comfortable referring me for this role? I'd be happy to share my resume and catch up on what you've been working on as well!

Thanks so much,
{user_name}""",
    ],
    "alumni": [
        """Hi {name},

I saw you're also an alumnus of {school}! I'm currently looking at opportunities at {company} and the {job_title} role seems like a great fit.

With my background in {user_skills}, I believe I could contribute meaningfully to the team. I'd love to connect with a fellow {school} alum and potentially get your thoughts on the role.

Would you be willing to chat briefly or refer me if you think I'd be a good fit?

Go {mascot}! 🎓

{user_name}""",
    ],
    "mutual_connection": [
        """Hi {name},

{mutual_contact} suggested I reach out to you. They mentioned you're doing great work at {company} in {topic}.

I'm a {user_role} with expertise in {user_skills} and I'm very interested in the {job_title} position. I'd love to learn more about the team and see if there might be a good fit.

Would you be open to a brief conversation?

Best,
{user_name}""",
    ],
}

FOLLOW_UP_TEMPLATES = [
    """Hi {name},

I wanted to follow up on my previous message about the {job_title} role at {company}. I understand you're busy, but I'd still love to connect if you have a moment.

If now isn't a good time, I completely understand. Either way, I appreciate your time.

Best,
{user_name}""",
    """Hi {name},

Just bumping this up in case it got buried. Still very interested in connecting about opportunities at {company}.

No pressure if you're swamped - just wanted to make sure my message didn't get lost.

Thanks!
{user_name}""",
]


def _get_company_interest_reason(company: str, job_analysis: JobAnalysis) -> str:
    """Generate a personalized reason for interest in the company."""
    reasons = [
        f"the innovative work you're doing in {job_analysis.role_category}",
        f"your commitment to {random.choice(['cutting-edge technology', 'professional development', 'innovation'])}",
        "the impact your team is making in the industry",
        "the strong engineering culture I've heard about",
    ]
    return random.choice(reasons)


def _get_specific_achievement(company: str) -> str:
    """Generate a plausible specific achievement mention."""
    achievements = [
        "your recent product launch",
        "the team's approach to solving complex problems",
        "how you've scaled your infrastructure",
        "your commitment to open source",
        "your focus on user experience",
    ]
    return random.choice(achievements)


def generate_cold_message(
    target_name: str,
    target_title: str,
    company: str,
    job_title: str,
    user_name: str,
    user_role: str,
    user_skills: list[str],
    message_type: str = "linkedin_connection",
    job_analysis: JobAnalysis | None = None,
    mutual_contact: str | None = None,
    school: str | None = None,
) -> NetworkingMessage:
    """Generate a personalized cold networking message.

    Args:
        target_name: Name of the person to contact
        target_title: Their job title
        company: Company name
        job_title: Job title you're applying for
        user_name: Your name
        user_role: Your current role
        user_skills: List of your skills
        message_type: Type of message to generate
        job_analysis: Optional job analysis for context
        mutual_contact: Optional mutual connection name
        school: Optional shared school for alumni messages

    Returns:
        NetworkingMessage with subject, body, tips, and follow-up
    """
    # Prepare template variables
    topic = job_analysis.role_category if job_analysis else "technology"
    top_skills = ", ".join(user_skills[:3]) if user_skills else "relevant technical skills"
    matching_skill = user_skills[0] if user_skills else "key technologies"
    company_interest = (
        _get_company_interest_reason(company, job_analysis)
        if job_analysis
        else "your innovative work"
    )
    specific_achievement = _get_specific_achievement(company)

    # Select template
    templates = COLD_MESSAGE_TEMPLATES.get(
        message_type, COLD_MESSAGE_TEMPLATES["linkedin_connection"]
    )
    template = random.choice(templates)

    # Format the message
    body = template.format(
        name=target_name.split()[0] if target_name else "there",
        full_name=target_name,
        company=company,
        job_title=job_title,
        user_name=user_name,
        user_role=user_role,
        user_skills=top_skills,
        top_skill=matching_skill,
        topic=topic,
        matching_skill=matching_skill,
        company_interest_reason=company_interest,
        specific_achievement=specific_achievement,
        contact_info="[Your Contact Information]",
    )

    # Generate subject line
    subjects = [
        f"Connection Request - Interested in {company}",
        f"Quick question about {company}",
        f"{user_role} interested in {job_title} opportunities",
        f"Connecting - {topic} professional",
    ]
    subject = random.choice(subjects)

    # Generate tips
    tips = [
        "Personalize the message further with specific details from their profile",
        "Keep it under 150 words for LinkedIn connection requests",
        "Mention a specific post or article they shared if relevant",
        "Follow up once after 5-7 days if no response",
        "Engage with their content before sending the message (like/comment)",
        "Be genuine - mention what specifically interests you about their work",
    ]

    # Generate follow-up
    follow_template = random.choice(FOLLOW_UP_TEMPLATES)
    follow_up = follow_template.format(
        name=target_name.split()[0] if target_name else "there",
        company=company,
        job_title=job_title,
        user_name=user_name,
    )

    return NetworkingMessage(
        subject=subject,
        body=body.strip(),
        tips=random.sample(tips, 3),
        follow_up=follow_up.strip(),
    )


def generate_referral_request(
    contact_name: str,
    company: str,
    job_title: str,
    user_name: str,
    user_role: str,
    user_skills: list[str],
    request_type: str = "colleague",
    job_analysis: JobAnalysis | None = None,
    mutual_contact: str | None = None,
    school: str | None = None,
    how_we_met: str | None = None,
) -> NetworkingMessage:
    """Generate a referral request message.

    Args:
        contact_name: Name of your contact
        company: Company name
        job_title: Job title
        user_name: Your name
        user_role: Your current role
        user_skills: List of your skills
        request_type: Type of referral request
        job_analysis: Optional job analysis
        mutual_contact: Optional mutual connection
        school: Optional shared school
        how_we_met: Optional reminder of how you know them

    Returns:
        NetworkingMessage with subject, body, tips, and follow-up
    """
    top_skills = ", ".join(user_skills[:3]) if user_skills else "relevant experience"

    # Select template based on type
    if request_type == "alumni" and school:
        template = random.choice(REFERRAL_TEMPLATES["alumni"])
        mascot = random.choice(["Tigers", "Bulldogs", "Eagles", "Bears", "Lions"])
        body = template.format(
            name=contact_name.split()[0] if contact_name else "there",
            company=company,
            job_title=job_title,
            user_name=user_name,
            user_skills=top_skills,
            school=school,
            mascot=mascot,
        )
    elif request_type == "mutual_connection" and mutual_contact:
        template = random.choice(REFERRAL_TEMPLATES["mutual_connection"])
        topic = job_analysis.role_category if job_analysis else "this area"
        body = template.format(
            name=contact_name.split()[0] if contact_name else "there",
            mutual_contact=mutual_contact,
            company=company,
            topic=topic,
            job_title=job_title,
            user_name=user_name,
            user_role=user_role,
            user_skills=top_skills,
        )
    else:
        template = random.choice(REFERRAL_TEMPLATES["colleague"])
        body = template.format(
            name=contact_name.split()[0] if contact_name else "there",
            company=company,
            job_title=job_title,
            user_name=user_name,
            user_skills=top_skills,
        )

    # Add personalization if we know how we met
    if how_we_met:
        body = body.replace(
            "I hope you're doing well!",
            f"It was great {how_we_met}! Hope you've been doing well since.",
        )

    # Generate subject
    subjects = [
        f"Referral Request - {job_title} at {company}",
        f"Quick favor - {job_title} application",
        f"Would you refer me for {job_title}?",
    ]
    subject = random.choice(subjects)

    # Generate tips specific to referrals
    tips = [
        "Make it easy for them to say yes - highlight your relevant qualifications upfront",
        "Offer to catch up first if you haven't spoken in a while",
        "Attach your resume to make the referral process easier",
        "Don't be pushy - give them an easy out if they're not comfortable",
        "If they refer you, send a thank you note regardless of the outcome",
        "Keep them updated on your application progress",
    ]

    # Follow-up for referral
    follow_up = f"""Hi {contact_name.split()[0] if contact_name else "there"},

Just wanted to follow up on the referral request for the {job_title} role. I completely understand if you're busy or not comfortable referring me - no pressure at all!

Either way, I'd love to catch up when you have time.

Thanks,
{user_name}"""

    return NetworkingMessage(
        subject=subject,
        body=body.strip(),
        tips=random.sample(tips, 3),
        follow_up=follow_up.strip(),
    )


def generate_linkedin_invite_note(
    target_name: str,
    company: str,
    job_title: str,
    user_role: str,
    user_skills: list[str],
) -> str:
    """Generate a short LinkedIn connection note (300 char limit).

    Args:
        target_name: Name of person
        company: Company name
        job_title: Job you're interested in
        user_role: Your role
        user_skills: Your top skills

    Returns:
        Short connection note under 300 characters
    """
    notes = [
        f"Hi {target_name.split()[0] if target_name else 'there'}, I'm a {user_role} with {user_skills[0] if user_skills else 'relevant'} experience, interested in the {job_title} role at {company}. Would love to connect!",
        f"Hello! I'm exploring opportunities at {company} and your background in {company} caught my attention. Would love to connect and learn from your experience.",
        f"Hi! I'm a {user_role} looking to break into {company}. Would value connecting with professionals like yourself in the space.",
    ]

    note = random.choice(notes)
    # Ensure it's under 300 characters
    if len(note) > 300:
        note = note[:297] + "..."

    return note
