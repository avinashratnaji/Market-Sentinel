"""
briefs/models.py

Models used by Market Briefs.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
)


# ==========================================================
# News
# ==========================================================

@dataclass(slots=True)
class NewsItem:

    title: str

    summary: str

    source: str

    impact: str

    score: int

    sectors: tuple[str, ...] = ()

    stocks: tuple[str, ...] = ()


# ==========================================================
# Sector
# ==========================================================

@dataclass(slots=True)
class SectorSnapshot:

    name: str

    value: float

    percent_change: float


# ==========================================================
# Stock
# ==========================================================

@dataclass(slots=True)
class StockSnapshot:

    symbol: str

    price: float

    percent_change: float


# ==========================================================
# Morning Brief
# ==========================================================

@dataclass(slots=True)
class MorningBrief:

    generated_at: datetime

    health_score: int

    market_sentiment: str

    confidence: int

    news: list[NewsItem] = field(default_factory=list)

    indices: list[IndexSnapshot] = field(default_factory=list)

    sectors: list[SectorSnapshot] = field(default_factory=list)

    gainers: list[StockSnapshot] = field(default_factory=list)

    losers: list[StockSnapshot] = field(default_factory=list)

    top_news: list[NewsArticle] = field(default_factory=list)