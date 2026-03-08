"""API request/response models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCall(BaseModel):
    tool_name: str
    tool_input: dict = Field(default_factory=dict)
    result: str | None = None
    duration_ms: int | None = None


class AgentTrace(BaseModel):
    agent_id: str
    division: str | None = None
    status: str = "running"  # running | complete | error
    message: str = ""
    tools_called: list[ToolCall] = Field(default_factory=list)
    confidence_score: float | None = None
    confidence_level: str | None = None
    duration_ms: int | None = None


class HitlEvent(BaseModel):
    finding: str
    agent_id: str
    confidence_score: float
    reason: str
    status: str = "pending"  # pending | approved | rejected


class IntegrationEvent(BaseModel):
    integration: str
    action: str
    status: str = "complete"
    detail: str = ""


class Message(BaseModel):
    id: str
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_traces: list[AgentTrace] = Field(default_factory=list)
    hitl_events: list[HitlEvent] = Field(default_factory=list)
    integration_events: list[IntegrationEvent] = Field(default_factory=list)
    sublab: str | None = None


class Chat(BaseModel):
    id: str
    title: str
    sublab: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: list[Message] = Field(default_factory=list)


class CreateChatRequest(BaseModel):
    sublab: str
    message: str


class SendMessageRequest(BaseModel):
    content: str


class SublabInfo(BaseModel):
    name: str
    description: str
    agents: list[str]
    divisions: list[str]
    examples: list[str]


class AgentInfo(BaseModel):
    id: str
    division: str
    status: str = "available"
    sublabs: list[str] = Field(default_factory=list)


class ToolInfo(BaseModel):
    name: str
    server: str
    description: str


class IntegrationInfo(BaseModel):
    name: str
    status: str = "available"  # available | connected | disabled
    description: str
