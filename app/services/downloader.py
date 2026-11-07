import os
import tempfile
import yt_dlp

# Create a secure temporary directory for downloaded media
TEMP_DIR = tempfile.mkdtemp()

def download_video_file(url: str) -> str:

    # Path to cookies.txt in this project root folder

    cookie_path = os.path.join(os.getcwd(), "cookies.txt")

    ydl_opts = {
        'format': 'bv*+ba/b',  # Best video + best audio with fallback
        'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',  # Automatically merge into a clean MP4 file using FFmpeg
    }

    # Automatically attach cookies if present to bypass bot detection/sign-in walls
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path

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