import re
import shutil
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import urlparse


import instaloader
import requests


MAX_FILE_SIZE = 100 * 1024 * 1024 #  100 MB

def download_carousel_item(url: str, index: int) -> str:
    """
    Download one seleccted Instagram carousel item.

    index starts from 1.
    Returns the path of the downloaded file.
    """

    # Step 1: Validate Instagram URL
    parsed = urlparse(url)

    if (
        parsed.scheme != "https"
        or parsed.hostname not in {
            "instagram.com",
            "www.instagram.com",
            "m.instagram.com",
        }
    ):
        raise ValueError("Invalid Instagram URL")

    parts = parsed.path.strip("/").split("/")

    if (
        len(parts) != 2
        or parts[0] != "p"
        or not re.fullmatch(r"[A-Za-z0-9_-]+", parts[1])

    ):
        raise ValueError("Invalid Instagram post URL")

    shortcode = parts[1]

    # Step 2 : Fetch Instagram post information
    loader  = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        save_metadata=False,
        quiet=True,
    )

    post = instaloader.Post.from_shortcode(
        loader.context,
        shortcode
    )

    if post.typename != "GraphSidecar":
        raise ValueError("This post is not a carousel")


    # Step 3: Retrieve carousel items
    nodes = list(post.get_sidecar_nodes())

    if index < 1 or index > len(nodes):
        raise ValueError("Invalid carousel item index")

    selected_item = nodes[index - 1]

    is_video = selected_item.is_video

    media_url = (
        selected_item.video_url
        if is_video
        else selected_item.display_url
    )

    if not media_url:
        raise ValueError("Selected media is unavailable")

    # step 4: validate the media download host
    media_parsed = urlparse(media_url)
    media_host = media_parsed.hostname or ""

    allowed_host = (
        media_host.endswith(".fbcdn.net")
        or media_host.endswith(".cdninstagram.com")
    )

    if media_parsed.scheme != "https" or not allowed_host:
        raise ValueError("Unexpected media download URL")

    # Step 5 : Create temporary directory
    temp_dir = Path(mkdtemp(prefix="instapull_carousel_"))

    try:
        with requests.get(
            media_url,
            stream=True,
            timeout=(10,45),
            allow_redirects=False,
        ) as response:

            if 300 <= response.status_code < 400:
                raise RuntimeError("Unexpected media redirect")

            response.raise_for_status()

            content_type = (
                response.headers.get("Content-Type", "")
                .split(";")[0]
                .strip()
                .lower()
            )

            if is_video:
                if content_type != "video/mp4":
                    raise ValueError("Unsupported video format")

                extension = "mp4"

            else:
                image_formats = {
                    "image/jpeg": "jpg",
                    "image/png": "png",
                    "image/webp": "webp",
                }

                extension = image_formats.get(content_type)

                if not extension:
                    raise ValueError("Unsupported image format")


            filename = f"carousel_item_{index}.{extension}"
            output_path = temp_dir / filename

            total_size = 0

            with output_path.open("wb") as file:
                for chunk in response.iter_content(65536):
                    if not chunk:
                        continue

                    total_size += len(chunk)

                    if total_size > MAX_FILE_SIZE:
                        raise ValueError("File exceeds size limit")

                    file.write(chunk)

        print(
            f"[CAROUSEL DOWNLOAD] Item {index} saved: {output_path}",
            flush=True,
        )

        return str(output_path)

    except Exception:
         shutil.rmtree(temp_dir, ignore_errors=True)
         raise




