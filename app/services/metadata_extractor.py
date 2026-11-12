import logging
from urllib.parse import urlparse

import yt_dlp
import instaloader

from app.services.ytdlp_options import base_opts

logger = logging.getLogger(__name__)

def detect_media_type(info: dict) -> str:
    """
    Detect Instagram media type from extracted metadata.
    """

    entries = info.get("entries")

    if entries is not None:
        valid_entries = [
            entry for entry in entries
            if isinstance(entry, dict)
        ]

        if len(valid_entries) > 1:
            return "carousel"
        
        if len(valid_entries) == 1:
            info = valid_entries[0]

    if info.get("vcodec") not in (None, "none"):
        return "video"
    
    if info.get("duration") is not None:
        return "video"
    
    formats = info.get("formats") or []

    for media_format in formats:
        if media_format.get("vcodec") not in (None, "none"):
            return "video"
        
    ext = (info.get("ext") or "").lower()

    if ext in {"jpg", "jpeg", "png", "webp"}:
        return "photo"
    
    # A reel/ URL indicates a video.9
    path = urlparse(info.get("webpage_url")or "").path
    if path.startswith("/reel/") or path.startswith("/reels/"):
        return "video"
    
    return "unkown"

def extract_video_metadata(url: str) -> dict:
    """
    Extract metadata for a video URL.
    """

    ydl_opts = {
        **base_opts(),
        "extract_flat": False,# Fast extraction without downloading
        "skip_download": True,
        "noplaylist": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return {}

        media_type = detect_media_type(info)

        if media_type == "unknown":
            logger.warning(
                "Unable to determine Instagram media type"
            )
            return {}

        first_entry = info

        if info.get("entries"):
            first_entry = next(
                (
                    entry
                    for entry in info["entries"]
                    if isinstance(entry, dict)
                ),
                info,
            )

        download_format = {
            "video": "mp4",
            "photo": "jpg",
            "carousel": "zip",
        }[media_type]

        return {
            "title": first_entry.get("title") or info.get("title"),
            "thumbnail": (
                first_entry.get("thumbnail")
                or info.get("thumbnail")
            ),
            "duration": first_entry.get("duration"),
            "author": (
                first_entry.get("uploader")
                or first_entry.get("channel")
                or info.get("uploader")
            ),
            "media_type": media_type,
            "download_format": download_format,
        }

    except Exception as error:
     logger.warning("yt-dlp extraction failed: %s", error)

     return extract_instagram_photo_metadata(url)


def extract_instagram_photo_metadata(url: str) -> dict:
    """
    Extract metadata for Instagram photo posts.
    Also identifies carousel posts.
    """

    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")

    if len(parts) != 2 or parts[0] != "p":
        return {}

    shortcode = parts[1]

    try:
        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            save_metadata=False,
            quiet=True,
        )

        post = instaloader.Post.from_shortcode(
            loader.context,
            shortcode,
        )

        if post.typename == "GraphImage":
            media_type = "photo"
            download_format = "jpg"

        elif post.typename == "GraphSidecar":
            media_type = "carousel"
            download_format = "zip"

        elif post.typename == "GraphVideo":
            media_type = "video"
            download_format = "mp4"

        else:
            return {}

        return {
            "title": (
                post.caption[:100]
                if post.caption
                else f"Instagram {media_type}"
            ),
            "thumbnail": post.url,
            "duration": None,
            "author": post.owner_username,
            "media_type": media_type,
            "download_format": download_format,
        }

    except Exception as error:
        print(f"Instagram metadata fallback error: {error}")
        return {}
