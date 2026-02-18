import re

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.constants import ALLOWED_TOOLS


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "agent")[:180]


def clean_tools(tool_names: list[str]) -> list[str]:
    cleaned: list[str] = []
    for name in tool_names:
        if name not in ALLOWED_TOOLS:
            raise HTTPException(status_code=422, detail=f"Unknown tool: {name}")
        if name not in cleaned:
            cleaned.append(name)
    return cleaned


class AgentWrite(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
    system_prompt: str = Field(default="You are a helpful agent.", min_length=1)
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_steps: int = Field(default=6, ge=1, le=20)
    tool_names: list[str] = Field(default_factory=list)
    memory_enabled: bool = True


class AgentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None


class VersionCreate(BaseModel):
    system_prompt: str = Field(min_length=1)
    model: str = Field(min_length=1, max_length=100)
    temperature: float = Field(ge=0, le=2)
    max_steps: int = Field(ge=1, le=20)
    tool_names: list[str] = Field(default_factory=list)
    memory_enabled: bool = True


class PublishRequest(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    tags: list[str] = Field(default_factory=list)
    slug: str | None = None
    version_id: int | None = None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=2, max_length=1000)


class ThreadCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class RunCreate(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
