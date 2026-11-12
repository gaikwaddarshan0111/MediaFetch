from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import urlparse
import shutil
import re
import instaloader
import requests

def download_instagram_photo(url: str) -> str:
    parsed = urlparse(url)

    if parsed.hostname not in {
        "instagram.com",
        "www.instagram.com",
        "m.instagram.com",
    }:
        raise ValueError("Only Instagram URLs are supported")
    
    parts = parsed.path.strip("/").split("/")

    if len(parts) !=2 or parts[0] != "p":
        raise ValueError("Expected an Instagram photo post URL")
    
    shortcode = parts[1]

    if not re.fullmatch(r"^[A-Za-z0-9_\-]+", shortcode):
        raise ValueError("Invalid Instagram shortcode")
    
    temp_dir = Path(mkdtemp(prefix="mediafetch+photo"))

    try:
        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            save_metadata=False,
            quiet=True,
        )

        post = instaloader.Post.from_shortcode(loader.context, shortcode,)

        if post.typename != "GraphImage":
            raise ValueError(
                "This endpoint supports single-photo posts only"
            )
        
        image_url = post.url
        output = temp_dir / "instagram_photo.jpg"

        with requests.get(
            image_url,
            stream=True,
            timeout=30,
        ) as response:
            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type" , ""
            ).lower()

            if not content_type.startswith("image/jpeg"):
                raise ValueError("Unexpected image format")
            
            with output.open("wb") as file:
                total = 0

                for chunk in response.iter_content(65536):
                    total += len(chunk)

                    if total > 25 * 1024 * 1024:
                        raise ValueError("Image exceeds size limit")
                    
                    file.write(chunk)

        return str(output)
    
    except Exception:
        shutil.rmtree(temp_dir, ignore_erors=True)
        raise 