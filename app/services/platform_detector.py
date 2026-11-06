from urllib.parse import urlparse

PLATFORM_DOMAINS = {
    "youtube": {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be"
    },

    "instagram": {
        "instagram.com",
        "www.instagram.com"
    }
}

def detect_platform(url: str):

    parsed_url = urlparse(url)

    domain = parsed_url.hostname

    if not domain:
        return None
    
    domain = domain.lower().rstrip(".")

    for platform, domains in PLATFORM_DOMAINS.items():

        if domain in domains:
            return platform
        
    return None