from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.schemas.video import VideoRequest, VideoResponse
from app.services.platform_detector import detect_platform
from app.services.metadata_extractor import extract_video_metadata
from app.services.downloader import download_video_file

# Do not put prefix here if main.py already adds /api/video
router = APIRouter(tags=["Video"])

@router.post("/info", response_model=VideoResponse)
def get_video_info(request: VideoRequest):
    detected_platform = detect_platform(str(request.url))

    if not detected_platform:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video platform"
        )
    
    if detected_platform != request.platform:
        raise HTTPException(
            status_code=400,
            detail="Selected platform does not match URL"
        )
    
    # Fetch real metadata
    metadata = extract_video_metadata(str(request.url))
    
    return VideoResponse(
        platform=detected_platform,
        url=str(request.url),
        status="validated",
        message="URL successfully validated",
        title=metadata.get("title"),
        thumbnail=metadata.get("thumbnail"),
        duration=metadata.get("duration"),
        author=metadata.get("author")
    )

@router.post("/download")
def download_video(request: VideoRequest):
    detected_platform = detect_platform(str(request.url))

    if not detected_platform:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video platform"
        )
    
    if detected_platform != request.platform:
        raise HTTPException(
            status_code=400,
            detail="Selected platform does not match URL"
        )
    
    try:
        file_path = download_video_file(str(request.url))

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate video file"
            )
            
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )