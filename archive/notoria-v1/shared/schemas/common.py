from typing import Any, Literal

from pydantic import BaseModel, Field

from shared.utils.ids import new_job_id

JobExecutionStatus = Literal["queued", "running", "failed", "completed", "accepted"]


class JobRequest(BaseModel):
    job_id: str = Field(default_factory=new_job_id)
    avatar_id: str = Field(..., min_length=1, max_length=120)
    script: str = Field(..., min_length=1)
    language: str = Field(default="fr", min_length=2, max_length=10)
    format: str = Field(default="mp4", min_length=2, max_length=20)
    params: dict[str, Any] = Field(default_factory=dict)


class JobResult(BaseModel):
    job_id: str
    status: JobExecutionStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ServiceHealth(BaseModel):
    service_name: str
    ok: bool
    gpu: dict[str, Any] = Field(default_factory=dict)
    version: str = "0.1.0"
