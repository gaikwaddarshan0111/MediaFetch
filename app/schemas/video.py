from pydantic import BaseModel, HttpUrl, Field

from typing import Literal, Optional

class VideoRequest(BaseModel):

    url: HttpUrl

    platform: Literal["youtube", "instagram"]

class VideoResponse(BaseModel):

    platform: str

    url: str

    status: str

    message: str

    title: Optional[str] = None

    thumbnail: Optional[str] = None

    duration: Optional[int] = None

    author: Optional[str] = None