from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    ok: bool = True
    service: str
    space: str


class KnowledgeInboxRequest(BaseModel):
    filename: str = Field(..., description="Target filename (will be created inside knowledge/kb/triage/inbox)")
    content: str = Field(..., description="Markdown body to drop into the inbox")
    metadata: Dict[str, Any] = Field(..., description="Metadata JSON sidecar")


class KnowledgeInboxResponse(BaseModel):
    path: str
    metadata_path: str
    warnings: Optional[list[str]] = None


class MemoryInboxRequest(BaseModel):
    source: str
    ts: datetime
    type: str
    content: str
    bucket: Optional[str] = None
    bucket_hint: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    participants: Optional[list[str]] = None
    participant_count: Optional[int] = None


class MemoryInboxResponse(BaseModel):
    path: str


class ParticipantActivityEntry(BaseModel):
    participant: str
    message_count: int
    bucket_count: int
    channel_count: int
    first_seen: str
    last_seen: str
    buckets: list[str]
    channels: list[str]
    sources: list[str]
    participant_mentions: int = 0


class ParticipantActivityResponse(BaseModel):
    start: str
    end: str
    bucket: Optional[str] = None
    limit: int
    total_participants: int
    results: list[ParticipantActivityEntry]


class OpsResponse(BaseModel):
    ok: bool
    operation: str
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str


class OpsBackfillResponse(BaseModel):
    ok: bool
    operation: str
    start_date: str
    end_date: str
    days: int
    collect: OpsResponse
    results: list[OpsResponse]


JSONMapping = Dict[str, Any]
