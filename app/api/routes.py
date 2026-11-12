from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import os
import shutil

from pathlib import Path

from app.schemas.video import VideoRequest, VideoResponse
from app.services.platform_detector import detect_platform
from app.services.metadata_extractor import extract_video_metadata
from app.services.downloader import download_video_file
from app.services.photo_downloader import download_instagram_photo

# Do not put prefix here if main.py already adds /api/video
router = APIRouter(tags=["Video"])


def validate_request(request: VideoRequest) -> str:
    detected_platform = detect_platform(str(request.url))

    if not detected_platform:
        raise HTTPException(status_code=400, detail="Only Instagram links are supported.")

    if detected_platform != request.platform:
        raise HTTPException(status_code=400, detail="Selected platform does not match URL.")

    return detected_platform




@router.post("/info", response_model=VideoResponse)
def get_video_info(request: VideoRequest):
    detected_platform = validate_request(request)

    metadata = extract_video_metadata(str(request.url))

    if not metadata:
        raise HTTPException(
            status_code=422,
            detail=(
                "Couldn't read this Instagram post. "
                "It may be private, removed, or temporarily unavailable."
            ),
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
    )


@router.post("/download")
def download_video(request: VideoRequest):
    validate_request(request)

    try:
        file_path = download_video_file(str(request.url))
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Couldn't download this video. It may be private, removed, or temporarily blocked."
        )

    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Failed to generate video file.")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="video/mp4",
        # Delete the temp file once it has been sent so the server disk doesn't fill up
        background=BackgroundTask(
            shutil.rmtree,
            str(Path(file_path).parent),
            ignore_errors=True
        )
    )


@router.post("/photo/download")
def download_photo(request: VideoRequest):
    validate_request(request)

    try:
        print(
            "[PHOTO DOWNLOAD] Starting Instagram photo download",
            flush=True
        )

        file_path = download_instagram_photo(
            str(request.url)
        )

        print(
            f"[PHOTO DOWNLOAD] File created: {file_path}",
            flush=True
        )

    except ValueError as error:
        print(
            f"[PHOTO DOWNLOAD] Validation error: {error}",
            flush=True
        )

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        import traceback

        print(
            "\n========== PHOTO DOWNLOAD ERROR ==========",
            flush=True
        )

        traceback.print_exception(
            type(error),
            error,
            error.__traceback__
        )

        print(
            "==========================================\n",
            flush=True
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve this Instagram photo."
        ) from error

    # Executed only after successful download
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=500,
            detail="Photo file was not generated."
        )

    return FileResponse(
        path=file_path,
        filename="instagram_photo.jpg",
        media_type="image/jpeg",
        background=BackgroundTask(
            shutil.rmtree,
            str(Path(file_path).parent),
            ignore_errors=True,
        ),
    )
