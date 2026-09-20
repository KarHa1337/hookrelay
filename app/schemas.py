from typing import Optional

from pydantic import BaseModel, HttpUrl


class ApiKeyOut(BaseModel):
    api_key: str


class RelayCreate(BaseModel):
    discord_webhook_url: HttpUrl
    label: Optional[str] = None
    secret: Optional[str] = None


class RelayOut(BaseModel):
    id: str
    label: Optional[str] = None
    post_url: str
    event_count: int
