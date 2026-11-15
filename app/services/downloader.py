import os
import shutil
import subprocess
import tempfile
import json

import yt_dlp

from app.services.ytdlp_options import base_opts


def is_compatible_mp4(file_path: str) -> bool:
    """Check whether the video can be delivered without re-encoding."""

    if not file_path.lower().endswith(".mp4"):
        return False

    if not shutil.which("ffprobe"):
        return False

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries",
                "stream=codec_type,codec_name,pix_fmt",
                "-of", "json",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )

        streams = json.loads(result.stdout).get("streams", [])

        videos = [
            s for s in streams
            if s.get("codec_type") == "video"
        ]

        audios = [
            s for s in streams
            if s.get("codec_type") == "audio"
        ]

        return (
            len(videos) == 1
            and videos[0].get("codec_name") == "h264"
            and videos[0].get("pix_fmt") == "yuv420p"
            and all(
                audio.get("codec_name") == "aac"
                for audio in audios
            )
        )

    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def download_video_file(url: str) -> str:
    # Isolated directory for each download

    temp_dir = tempfile.mkdtemp(prefix="mediafetch_")

    try:
        options = {
            **base_opts(),
            "format": "best[ext=mp4]/best",
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


        if is_compatible_mp4(source):
            print(
                "[DOWNLOAD] Compatible MP4 detected. Skipping FFmpeg.",
                flush=True,
            )

            os.replace(source, output)
            return output

        print(
            "[DOWNLOAD] Conversion required. Starting FFmpeg.",
            flush=True,
        )


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