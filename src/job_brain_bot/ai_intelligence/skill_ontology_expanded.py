"""Expanded skill ontology with certifications and learning paths.

Maps roles to required skills, recommended certifications,
and learning resources.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class SkillPathway:
    """Learning pathway for a skill."""

    skill: str
    beginner_resources: list[str] = field(default_factory=list)
    intermediate_resources: list[str] = field(default_factory=list)
    advanced_resources: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    estimated_hours: int = 0


@dataclass(slots=True)
class CareerTrack:
    """Career progression track with skill requirements."""

    role: str
    entry_skills: list[str] = field(default_factory=list)
    mid_skills: list[str] = field(default_factory=list)
    senior_skills: list[str] = field(default_factory=list)
    recommended_certifications: list[str] = field(default_factory=list)
    complementary_skills: list[str] = field(default_factory=list)


# Comprehensive skill database
SKILL_DATABASE: dict[str, SkillPathway] = {
    # Programming Languages
    "python": SkillPathway(
        skill="Python",
        beginner_resources=[
            "Python for Everybody (Coursera)",
            "Automate the Boring Stuff",
            "Official Python Tutorial",
        ],
        intermediate_resources=[
            "Effective Python",
            "Python Cookbook",
            "Flask/Django Documentation",
        ],
        advanced_resources=[
            "High Performance Python",
            "Python Concurrency",
            "Machine Learning with Python",
        ],
        certifications=["PCAP - Python Certified Associate Programmer", "PCPP - Python Certified Professional"],
        estimated_hours=80,
    ),
    "javascript": SkillPathway(
        skill="JavaScript",
        beginner_resources=["JavaScript.info", "Eloquent JavaScript", "freeCodeCamp"],
        intermediate_resources=["You Don't Know JS", "JavaScript: The Good Parts"],
        advanced_resources=["JavaScript Performance", "Node.js Design Patterns"],
        certifications=["JavaScript Institute Certification"],
        estimated_hours=60,
    ),
    "typescript": SkillPathway(
        skill="TypeScript",
        beginner_resources=["TypeScript Handbook", "Total TypeScript"],
        intermediate_resources=["Effective TypeScript", "TypeScript Deep Dive"],
        advanced_resources=["Advanced TypeScript Patterns"],
        certifications=[],
        estimated_hours=40,
    ),
    # Frontend
    "react": SkillPathway(
        skill="React",
        beginner_resources=["React Documentation", "React Tutorial", "Scrimba React Course"],
        intermediate_resources=["React Patterns", "Epic React by Kent C. Dodds"],
        advanced_resources=["React Internals", "Advanced React Patterns"],
        certifications=["Meta Front-End Developer"],
        estimated_hours=50,
    ),
    "angular": SkillPathway(
        skill="Angular",
        beginner_resources=["Angular Documentation", "Angular University"],
        intermediate_resources=["Pro Angular", "RxJS with Angular"],
        advanced_resources=["Angular Performance", "Enterprise Angular"],
        certifications=["Google Angular Certification"],
        estimated_hours=60,
    ),
    # Backend
    "node.js": SkillPathway(
        skill="Node.js",
        beginner_resources=["Node.js Documentation", "NodeSchool"],
        intermediate_resources=["Node.js Design Patterns", "Web Development with Node"],
        advanced_resources=["Node.js Internals", "Node.js Microservices"],
        certifications=["OpenJS Node.js Certification"],
        estimated_hours=50,
    ),
    "sql": SkillPathway(
        skill="SQL",
        beginner_resources=["SQLZoo", "W3Schools SQL", "Mode Analytics Tutorial"],
        intermediate_resources=["SQL Cookbook", "Learning SQL"],
        advanced_resources=["High Performance SQL", "SQL Optimization"],
        certifications=["Oracle SQL Certification", "Microsoft SQL Certification"],
        estimated_hours=40,
    ),
    # Cloud & DevOps
    "aws": SkillPathway(
        skill="AWS",
        beginner_resources=["AWS Cloud Practitioner Essentials", "AWS Free Tier Labs"],
        intermediate_resources=["AWS Solutions Architect", "AWS Developer Guide"],
        advanced_resources=["AWS Advanced Networking", "AWS Security Specialty"],
        certifications=[
            "AWS Cloud Practitioner",
            "AWS Solutions Architect Associate",
            "AWS Solutions Architect Professional",
            "AWS Security Specialty",
        ],
        estimated_hours=120,
    ),
    "azure": SkillPathway(
        skill="Azure",
        beginner_resources=["Azure Fundamentals", "Microsoft Learn Azure"],
        intermediate_resources=["Azure Administrator", "Azure Developer"],
        advanced_resources=["Azure Solutions Architect", "Azure DevOps Expert"],
        certifications=[
            "AZ-900: Azure Fundamentals",
            "AZ-104: Azure Administrator",
            "AZ-204: Azure Developer",
            "AZ-305: Azure Solutions Architect",
        ],
        estimated_hours=120,
    ),
    "docker": SkillPathway(
        skill="Docker",
        beginner_resources=["Docker Documentation", "Docker Getting Started"],
        intermediate_resources=["Docker Deep Dive", "Docker for Developers"],
        advanced_resources=["Docker Security", "Docker Orchestration"],
        certifications=["Docker Certified Associate"],
        estimated_hours=30,
    ),
    "kubernetes": SkillPathway(
        skill="Kubernetes",
        beginner_resources=["Kubernetes Basics", "Katacoda Kubernetes"],
        intermediate_resources=["Kubernetes Up and Running", "CKA Prep"],
        advanced_resources=["Kubernetes Patterns", "Kubernetes Security"],
        certifications=["CKA - Certified Kubernetes Administrator", "CKAD - Certified Kubernetes Application Developer"],
        estimated_hours=80,
    ),
    # Cybersecurity
    "network security": SkillPathway(
        skill="Network Security",
        beginner_resources=["Network Security Basics", "CompTIA Network+"],
        intermediate_resources=["CCNA Security", "Firewall Configuration"],
        advanced_resources=["Advanced Network Defense", "Zero Trust Architecture"],
        certifications=["CCNA", "CCNP Security", "CompTIA Security+"],
        estimated_hours=100,
    ),
    "siem": SkillPathway(
        skill="SIEM",
        beginner_resources=["Splunk Fundamentals", "Elastic SIEM Guide"],
        intermediate_resources=["Splunk Core Certified", "QRadar Fundamentals"],
        advanced_resources=["SIEM Architecture", "Advanced Threat Detection"],
        certifications=["Splunk Core Certified", "IBM QRadar Certification"],
        estimated_hours=60,
    ),
    "penetration testing": SkillPathway(
        skill="Penetration Testing",
        beginner_resources=["Penetration Testing Basics", "TryHackMe"],
        intermediate_resources=["eJPT Certification Prep", "Hack The Box"],
        advanced_resources=["OSCP Prep", "Advanced Penetration Testing"],
        certifications=["eJPT", "CEH", "OSCP", "GPEN"],
        estimated_hours=150,
    ),
    "incident response": SkillPathway(
        skill="Incident Response",
        beginner_resources=["Incident Response Basics", "NIST SP 800-61"],
        intermediate_resources=["GCIH Prep", "Digital Forensics"],
        advanced_resources=["Advanced Incident Response", "Threat Hunting"],
        certifications=["GCIH", "GCFA", "GCTI"],
        estimated_hours=100,
    ),
    # Data
    "machine learning": SkillPathway(
        skill="Machine Learning",
        beginner_resources=["Andrew Ng ML Course", "Fast.ai"],
        intermediate_resources=["Hands-On ML", "Pattern Recognition and ML"],
        advanced_resources=["Deep Learning Book", "ML System Design"],
        certifications=["AWS ML Specialty", "Google Professional ML Engineer"],
        estimated_hours=150,
    ),
    "data analysis": SkillPathway(
        skill="Data Analysis",
        beginner_resources=["Data Analysis with Python", "Google Data Analytics"],
        intermediate_resources=["Python for Data Analysis", "Storytelling with Data"],
        advanced_resources=["Advanced Analytics", "Predictive Analytics"],
        certifications=["Google Data Analytics", "IBM Data Analyst"],
        estimated_hours=60,
    ),
    # Mobile
    "react native": SkillPathway(
        skill="React Native",
        beginner_resources=["React Native Docs", "React Native in Action"],
        intermediate_resources=["Advanced React Native", "React Native Performance"],
        advanced_resources=["React Native Architecture"],
        certifications=["Meta React Native"],
        estimated_hours=50,
    ),
}

# Career tracks with skill progressions
CAREER_TRACKS: dict[str, CareerTrack] = {
    "frontend": CareerTrack(
        role="Frontend Developer",
        entry_skills=["html", "css", "javascript", "git"],
        mid_skills=["react" "typescript", "css frameworks", "testing", "ci/cd"],
        senior_skills=["react" "performance", "architecture", "mentoring", "system design"],
        recommended_certifications=["Meta Front-End Developer"],
        complementary_skills=["ui/ux", "accessibility", "seo"],
    ),
    "backend": CareerTrack(
        role="Backend Developer",
        entry_skills=["python" "javascript" "sql", "git", "rest apis"],
        mid_skills=["python" "databases", "caching", "message queues", "microservices"],
        senior_skills=["python" "system design", "scalability", "security", "mentoring"],
        recommended_certifications=["AWS Solutions Architect", "Docker Certified"],
        complementary_skills=["devops", "cloud", "distributed systems"],
    ),
    "devops": CareerTrack(
        role="DevOps Engineer",
        entry_skills=["linux", "git", "python" "bash", "cloud basics"],
        mid_skills=["docker", "kubernetes", "ci/cd", "iac", "monitoring"],
        senior_skills=["kubernetes" "security", "platform engineering", "sre practices"],
        recommended_certifications=[
            "AWS Solutions Architect",
            "CKA",
            "Docker Certified",
        ],
        complementary_skills=["programming", "networking", "security"],
    ),
    "cybersecurity": CareerTrack(
        role="Security Analyst",
        entry_skills=["networking", "linux", "security basics", "python"],
        mid_skills=["siem", "incident response", "vulnerability assessment", "threat hunting"],
        senior_skills=["penetration testing" "forensics", "security architecture", "mentoring"],
        recommended_certifications=[
            "CompTIA Security+",
            "CEH",
            "CISSP",
            "GCIH",
        ],
        complementary_skills=["programming", "cloud security", "compliance"],
    ),
    "fullstack": CareerTrack(
        role="Full Stack Developer",
        entry_skills=["javascript", "python" "html", "css", "sql", "git"],
        mid_skills=["react" "node.js", "databases", "cloud services", "testing"],
        senior_skills=["react" "architecture", "performance", "security", "leadership"],
        recommended_certifications=["AWS Developer", "Meta Full-Stack"],
        complementary_skills=["devops", "product management", "ux"],
    ),
    "data": CareerTrack(
        role="Data Scientist",
        entry_skills=["python" "sql", "statistics", "pandas", "numpy"],
        mid_skills=["machine learning", "data visualization", "big data", "cloud ml"],
        senior_skills=["machine learning" "deep learning", "mlops", "leadership"],
        recommended_certifications=["Google ML Engineer", "AWS ML Specialty"],
        complementary_skills=["domain expertise", "communication", "engineering"],
    ),
}

# Certification details
CERTIFICATION_DETAILS: dict[str, dict] = {
    "CompTIA Security+": {
        "provider": "CompTIA",
        "level": "Entry",
        "cost": "$370",
        "validity": "3 years",
        "topics": ["Threats", "Vulnerabilities", "Identity", "Cryptography"],
    },
    "CEH": {
        "provider": "EC-Council",
        "level": "Intermediate",
        "cost": "$1,199",
        "validity": "3 years",
        "topics": ["Ethical Hacking", "Penetration Testing", "Tools"],
    },
    "CISSP": {
        "provider": "ISC2",
        "level": "Advanced",
        "cost": "$749",
        "validity": "3 years",
        "topics": ["Security", "Risk Management", "Architecture"],
        "experience_required": "5 years",
    },
    "AWS Cloud Practitioner": {
        "provider": "AWS",
        "level": "Entry",
        "cost": "$100",
        "validity": "3 years",
        "topics": ["Cloud Concepts", "AWS Services", "Security"],
    },
    "AWS Solutions Architect Associate": {
        "provider": "AWS",
        "level": "Intermediate",
        "cost": "$150",
        "validity": "3 years",
        "topics": ["Architecture", "High Availability", "Security"],
    },
    "CKA": {
        "provider": "CNCF",
        "level": "Intermediate",
        "cost": "$395",
        "validity": "3 years",
        "topics": ["Kubernetes", "Cluster Management", "Troubleshooting"],
    },
    "PCAP": {
        "provider": "Python Institute",
        "level": "Intermediate",
        "cost": "$295",
        "validity": "Lifetime",
        "topics": ["Python", "OOP", "Modules", "Exceptions"],
    },
    "Meta Front-End Developer": {
        "provider": "Meta",
        "level": "Entry-Intermediate",
        "cost": "Coursera Subscription",
        "validity": "Lifetime",
        "topics": ["React", "HTML/CSS", "JavaScript", "UX"],
    },
}


def get_skill_pathway(skill: str) -> Optional[SkillPathway]:
    """Get learning pathway for a skill."""
    skill_lower = skill.lower()
    return SKILL_DATABASE.get(skill_lower)


def get_career_track(role: str) -> Optional[CareerTrack]:
    """Get career track for a role category."""
    role_lower = role.lower()

    # Map variations to standard tracks
    track_mapping = {
        "frontend": "frontend",
        "front-end": "frontend",
        "backend": "backend",
        "back-end": "backend",
        "fullstack": "fullstack",
        "full-stack": "fullstack",
        "devops": "devops",
        "sre": "devops",
        "cybersecurity": "cybersecurity",
        "security": "cybersecurity",
        "data": "data",
        "data science": "data",
        "ml": "data",
    }

    standard = track_mapping.get(role_lower)
    if standard:
        return CAREER_TRACKS.get(standard)
    return None


def get_certification_info(cert_name: str) -> Optional[dict]:
    """Get detailed information about a certification."""
    for cert_key, info in CERTIFICATION_DETAILS.items():
        if cert_name.lower() in cert_key.lower() or cert_key.lower() in cert_name.lower():
            return {**info, "name": cert_key}
    return None
