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
    """
    Download Instagram video with Vercel-compatible fallback.

    - Prefer H.264/AAC MP4.
    - Skip FFmpeg when the file is compatible.
    - Allow direct MP4 delivery when FFmpeg is unavailable.
    - Convert incompatible formats when FFmpeg is available.
    - Clean up temporary files if downloading fails.
    """

    temp_dir = tempfile.mkdtemp(prefix="mediafetch_")

    try:
        ffmpeg_available = shutil.which("ffmpeg") is not None
        ffprobe_available = shutil.which("ffprobe") is not None

        print(
            f"[ENV] FFmpeg: {ffmpeg_available}, "
            f"FFprobe: {ffprobe_available}",
            flush=True,
        )

        options = {
            **base_opts(),
            "format": (
                "best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
                "best[ext=mp4][vcodec^=avc1]/"
                "best[ext=mp4]/best"
            ),
            "outtmpl": os.path.join(
                temp_dir,
                "source.%(ext)s"
            ),
            "noplaylist": True,
            "merge_output_format": "mp4",
        }

        # Download media
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

            if not info:
                raise RuntimeError(
                    "Instagram returned no video information."
                )

            source = ydl.prepare_filename(info)

        if not os.path.isfile(source):
            raise RuntimeError(
                "Downloaded source video not found."
            )

        print(
            f"[DOWNLOAD] Source: {source}",
            flush=True,
        )

        output = os.path.join(
            temp_dir,
            "instagram.mp4"
        )

        # Case 1: Already compatible with mobile playback
        if ffprobe_available and is_compatible_mp4(source):
            print(
                "[DOWNLOAD] Compatible MP4 detected. "
                "Skipping conversion.",
                flush=True,
            )

            os.replace(source, output)
            return output

        # Case 2: Vercel does not have FFmpeg
        if not ffmpeg_available:
            if source.lower().endswith(".mp4"):
                print(
                    "[DOWNLOAD] FFmpeg unavailable. "
                    "Returning existing MP4.",
                    flush=True,
                )

                os.replace(source, output)
                return output

            raise RuntimeError(
                "Downloaded video is not MP4 and "
                "FFmpeg is unavailable."
            )

        # Case 3: Convert using FFmpeg
        print(
            "[DOWNLOAD] Starting FFmpeg conversion.",
            flush=True,
        )

        command = [
            "ffmpeg",
            "-y",
            "-i", source,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-movflags", "+faststart",
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
            raise RuntimeError(
                "FFmpeg conversion failed."
            )

        print(
            "[DOWNLOAD] Conversion completed.",
            flush=True,
        )

        return output

    except Exception as error:
        print(
            f"[DOWNLOAD ERROR] {type(error).__name__}: {error}",
            flush=True,
        )

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        raise
