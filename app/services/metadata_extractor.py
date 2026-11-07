import yt_dlp

from app.services.ytdlp_options import base_opts

def extract_video_metadata(url: str) -> dict:
    ydl_opts = {
        **base_opts(),
        "extract_flat": True ,# Fast extraction without downloading
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "author": info.get("uploader") or info.get("channel"),
            }
    except Exception as e:
        print(f"Metadata extraction error: {e}")
        return {}