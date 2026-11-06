import os
import tempfile
import yt_dlp

# Create a secure temporary directory for downloaded media
TEMP_DIR = tempfile.mkdtemp()

def download_video_file(url: str) -> str:
    ydl_opts = {
        'format': 'bv*+ba/b',  # Best video + best audio with fallback
        'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',  # Automatically merge into a clean MP4 file using FFmpeg
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        print(f"Download error: {e}")
        raise e