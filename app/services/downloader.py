import os
import shutil
import subprocess
import tempfile

import yt_dlp

from app.services.ytdlp_options import base_opts


def download_video_file(url: str) -> str:
    # Isolated directory for each download

    temp_dir = tempfile.mkdtemp(prefix="mediafetch_")

    try:
        options = {
            **base_opts(),
            "format": "best",
            "outtmpl": os.path.join(
                temp_dir, "source.%(ext)s"
            ),
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            source = ydl.prepare_filename(info)

        if not os.path.isfile(source):
            raise RuntimeError("Source video not found")
        
        output = os.path.join(temp_dir, "instagram.mp4")

        command = [
            "ffmpeg", "-y",
            "-i", source,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-profile:a", "aac_low",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-movflags","+faststart",
            output,
        ]

        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,

        )

        if not os.path.isfile(output):
            raise RuntimeError("Conversion failed")
        return output
    
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise