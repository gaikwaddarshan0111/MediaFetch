
import os
import shutil
import traceback
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.schemas.video import VideoRequest, VideoResponse
from app.services.platform_detector import detect_platform
from app.services.metadata_extractor import extract_video_metadata
from app.services.downloader import download_video_file
from app.services.photo_downloader import download_instagram_photo
from app.schemas.video import CarouselItemRequest
from app.services.carousel_item_downloader import download_carousel_item

# Prefix /api/video is already configured in main.py
router = APIRouter(tags=["Media"])


def validate_request(request: VideoRequest) -> str:
    detected_platform = detect_platform(str(request.url))

    if detected_platform != "instagram":
        raise HTTPException(
            status_code=400,
            detail="Only Instagram URLs are supported."
        )

    if detected_platform != request.platform:
        raise HTTPException(
            status_code=400,
            detail="Selected platform does not match URL."
        )

    return detected_platform


def create_file_response(file_path: str, filename: str, media_type: str):
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=500,
            detail="Downloaded file was not generated."
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        background=BackgroundTask(
            shutil.rmtree,
            str(Path(file_path).parent),
            ignore_errors=True,
        ),
    )


# --------------------------------------------------
# GET MEDIA INFORMATION
# --------------------------------------------------

@router.post("/info", response_model=VideoResponse)
def get_video_info(request: VideoRequest):
    detected_platform = validate_request(request)

    metadata = extract_video_metadata(str(request.url))

    if not metadata:
        raise HTTPException(
            status_code=422,
            detail="Unable to retrieve Instagram media information."
        )

    print(
        f"[INFO] Detected media: {metadata.get('media_type')}",
        flush=True
    )

    return VideoResponse(
        platform=detected_platform,
        url=str(request.url),
        status="validated",
        message="Instagram media successfully detected",
        title=metadata.get("title"),
        thumbnail=metadata.get("thumbnail"),
        duration=metadata.get("duration"),
        author=metadata.get("author"),
        media_type=metadata["media_type"],
        download_format=metadata["download_format"],
        carousel_items=metadata.get("carousel_items", []),
    )


# --------------------------------------------------
# UNIFIED MEDIA DOWNLOAD
# --------------------------------------------------

@router.post("/download")
def download_media(request: VideoRequest):
    validate_request(request)

    url = str(request.url)

    metadata = extract_video_metadata(url)

    if not metadata:
        raise HTTPException(
            status_code=422,
            detail="Unable to identify Instagram media."
        )

    media_type = metadata.get("media_type")

    print(
        f"[DOWNLOAD] Detected type: {media_type}",
        flush=True
    )

    if media_type == "carousel":
        raise HTTPException(
            status_code=501,
            detail="Carousel download is not supported yet."
        )

    try:
        if media_type == "photo":

            print("[DOWNLOAD] Starting photo download", flush=True)

            file_path = download_instagram_photo(url)

            filename = "instagram-photo.jpg"
            content_type = "image/jpeg"

        elif media_type == "video":

            print("[DOWNLOAD] Starting video download", flush=True)

            file_path = download_video_file(url)

            filename = os.path.basename(file_path)
            content_type = "video/mp4"

        else:
            raise HTTPException(
                status_code=422,
                detail="Unsupported Instagram media type."
            )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        print(
            "\n========== MEDIA DOWNLOAD ERROR ==========",
            flush=True
        )
        traceback.print_exc()
        print("==========================================\n", flush=True)

        raise HTTPException(
            status_code=502,
            detail="Unable to download Instagram media."
        ) from error

    print(
        f"[DOWNLOAD] File ready: {file_path}",
        flush=True
    )

    return create_file_response(
        file_path=file_path,
        filename=filename,
        media_type=content_type,
    )


# --------------------------------------------------
# LEGACY PHOTO ENDPOINT
# Retained for frontend compatibility
# --------------------------------------------------

@router.post("/photo/download")
def download_photo(request: VideoRequest):
    validate_request(request)

    try:
        file_path = download_instagram_photo(str(request.url))

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve this Instagram photo."
        ) from error

    return create_file_response(
        file_path=file_path,
        filename="instagram-photo.jpg",
        media_type="image/jpeg",
    )

# --------------------------------------------------
# INDIVIDUAL CAROUSEL ITEM DOWNLOAD
# --------------------------------------------------

@router.post("/carousel/item/download")
def download_single_carousel_item(request: CarouselItemRequest):
    validate_request(request)

    print(
        f"[CAROUSEL ITEM DOWNLOAD] Request received for item {request.index}",
        flush=True
    )

    try:
        file_path = download_carousel_item(
            url=str(request.url),
            index=request.index
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )from error

    except Exception as error:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="Unable to download carousel item."
        )from error

    extension = Path(file_path).suffix.lower()

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
    }

    media_type = media_types.get(extension)

    if not media_type:
        shutil.rmtree(
            str(Path(file_path).parent),
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail="Unsupported downloaded file format."
        )

    return create_file_response(
        file_path=file_path,
        filename=f"instagram-{request.index}{extension}",
        media_type=media_type
    )