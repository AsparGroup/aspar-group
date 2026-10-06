from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ServiceCategory(str, Enum):
    video = "video"
    tts = "tts"
    lipsync = "lipsync"
    enhance = "enhance"
    qa = "qa"


class ServiceType(str, Enum):
    local = "local"
    saas = "saas"


class RegistryServiceBase(BaseModel):
    service_name: str = Field(..., min_length=2, max_length=120)
    category: ServiceCategory
    type: ServiceType
    base_url: HttpUrl
    auth_type: str = Field(default="none", min_length=2, max_length=50)
    auth_secret_ref: str | None = Field(default=None, max_length=255)
    endpoints: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, Any] = Field(default_factory=dict)
    fallback_service: str | None = Field(default=None, max_length=120)
    enabled: bool = True


class RegistryServiceCreate(RegistryServiceBase):
    pass


class RegistryServicePatch(BaseModel):
    service_name: str | None = Field(default=None, min_length=2, max_length=120)
    category: ServiceCategory | None = None
    type: ServiceType | None = None
    base_url: HttpUrl | None = None
    auth_type: str | None = Field(default=None, min_length=2, max_length=50)
    auth_secret_ref: str | None = Field(default=None, max_length=255)
    endpoints: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None
    fallback_service: str | None = Field(default=None, max_length=120)
    enabled: bool | None = None


class RegistryServiceResponse(RegistryServiceBase):
    id: int

    class Config:
        from_attributes = True
