from pydantic import BaseModel, HttpUrl, Field

from typing import Literal, Optional

class VideoRequest(BaseModel):

    url: HttpUrl

    platform: Literal["instagram"]

class CarouselItem(BaseModel):

    index: int
    media_type: Literal["photo", "video"]
    thumbnail: str

class CarouselItemRequest(VideoRequest):
    index: int = Field(ge=1, le=20)

class VideoResponse(BaseModel):

    platform: str

    url: str

    status: str

    message: str

    title: Optional[str] = None

    thumbnail: Optional[str] = None

    duration: Optional[int] = None

    author: Optional[str] = None

    media_type: Literal["photo","video","carousel"]

    download_format: Literal["jpg", "mp4", "individual"]

    carousel_items: list[CarouselItem] = Field(default_factory=list)