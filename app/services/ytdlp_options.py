import os

COOKIE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cookies.txt"
)


def base_opts() -> dict:
    opts = {"noplaylist": True, "quiet": True}
    if os.path.exists(COOKIE_PATH):
        opts["cookiefile"] = COOKIE_PATH

    return opts