"""
news/models.py

News models.

Author : Market Sentinel
"""

from __future__ import annotations
from dataclasses import field
from dataclasses import dataclass
from datetime import datetime
from market_sentinel.news.enums import (
    NewsCategory,
    NewsImportance,
)

@dataclass(slots=True)
class NewsArticle:

    title: str

    summary: str

    source: str

    url: str

    published_at: datetime | None = None

    impact: int = 0

    sentiment: str = "Neutral"

    sectors: list[str] | None = None

    symbols: list[str] | None = None

    duplicate: bool = False

    category: NewsCategory = NewsCategory.GENERAL

    importance: int = 0

    entities: list[str] = field(default_factory=list)

    score: int = 0