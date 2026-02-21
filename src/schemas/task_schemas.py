from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class CreateTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model_config = ConfigDict(str_strip_whitespace=True)


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class TaskStatusResponse(BaseModel):
    task_id: str
    prompt: str
    status: str
    result: Optional[str] = None
    agent_logs: List[dict] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ApproveTaskResponse(BaseModel):
    task_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    task_id: Optional[str] = None
    error_code: Optional[str] = None