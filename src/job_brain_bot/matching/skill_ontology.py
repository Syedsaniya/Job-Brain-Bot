ROLE_SKILL_ONTOLOGY: dict[str, set[str]] = {
    "cybersecurity": {
        "siem",
        "splunk",
        "soc",
        "incident response",
        "network security",
        "threat hunting",
        "vulnerability assessment",
        "firewall",
        "python",
        "linux",
    },
    "backend": {
        "python",
        "java",
        "golang",
        "sql",
        "postgresql",
        "redis",
        "docker",
        "kubernetes",
        "api",
        "microservices",
    },
    "frontend": {
        "javascript",
        "typescript",
        "react",
        "next.js",
        "html",
        "css",
        "redux",
        "testing library",
        "webpack",
        "ui",
    },
}


def normalize_role_group(role: str) -> str:
    role_l = role.lower()
    if any(token in role_l for token in ("security", "soc", "cyber")):
        return "cybersecurity"
    if any(token in role_l for token in ("frontend", "front-end", "ui")):
        return "frontend"
    if any(token in role_l for token in ("backend", "back-end", "api", "server")):
        return "backend"
    return "backend"


def get_role_skill_set(role: str) -> set[str]:
    return ROLE_SKILL_ONTOLOGY.get(normalize_role_group(role), set())
