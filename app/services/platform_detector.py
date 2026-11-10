from urllib.parse import urlparse

PLATFORM_DOMAINS = {
    "instagram": {
        "instagram.com",
        "www.instagram.com",
        "m.instagram.com",
    }
}


def detect_platform(url: str):
    domain = urlparse(url).hostname

    if not domain:
        return None

    domain = domain.lower().rstrip(".")

    for platform, domains in PLATFORM_DOMAINS.items():
        if domain in domains:
            return platform

    return None