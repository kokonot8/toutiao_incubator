from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SampleArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account: str = Field(index=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StyleProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account: str = Field(index=True, unique=True)
    profile_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account: str = Field(index=True)
    topic: str
    title: str
    content: str
    review_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)
