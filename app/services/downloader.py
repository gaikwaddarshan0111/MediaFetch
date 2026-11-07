import os
import tempfile
import yt_dlp

from app.services.ytdlp_options import base_opts

# Create a secure temporary directory for downloaded media
TEMP_DIR = tempfile.mkdtemp()

def download_video_file(url: str) -> str:

    ydl_opts = {
        **base_opts(),
        "format": "bv*+ba/b",
        "outtmpl": os.path.join(TEMP_DIR, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Ensure path points to the merged .mp4 file
            base, _ = os.path.splitext(filename)
            mp4_path = base + ".mp4"
            if os.path.exists(mp4_path):
                return mp4_path

            return filename
    except Exception as e:
        print(f"Download error: {e}")
        raise e