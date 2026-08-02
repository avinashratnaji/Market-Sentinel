"""
briefs/morning.py

Morning Brief Builder.

Author : Market Sentinel
"""

from __future__ import annotations

from datetime import datetime

from market_sentinel.briefs.health import (
    MarketHealthEngine,
)

from market_sentinel.briefs.models import (
    MorningBrief,
)

from market_sentinel.providers.angelone.indices import (
    IndianIndicesProvider,
)

from market_sentinel.providers.angelone.sectors import (
    SectorProvider,
)

from market_sentinel.providers.angelone.gainers import (
    GainersProvider,
)

from market_sentinel.providers.angelone.losers import (
    LosersProvider,
)

from market_sentinel.news.aggregator import (
    NewsAggregator,
)

from market_sentinel.news.classifier import (
    NewsClassifier,
)

from market_sentinel.news.entity_extractor import (
    EntityExtractor,
)

from market_sentinel.news.sector_mapper import (
    SectorMapper,
)

from market_sentinel.news.scoring_engine import (
    NewsScoringEngine,
)

from market_sentinel.news.summary_builder import (
    NewsSummaryBuilder,
)

from market_sentinel.news.sources.yahoo_finance.provider import (
    YahooFinanceProvider,
)


class MorningBriefBuilder:

    def __init__(self):

        self.indices = IndianIndicesProvider()

        self.sectors = SectorProvider()

        self.gainers = GainersProvider()

        self.losers = LosersProvider()

        self.health = MarketHealthEngine()

    def build(self) -> MorningBrief:

        brief = MorningBrief(

            generated_at=datetime.now(),

            health_score=0,

            market_sentiment="Unknown",

            confidence=0,

            top_news=[],

            indices=self.indices.fetch(),

            sectors=self.sectors.fetch(),

            gainers=self.gainers.fetch(),

            losers=self.losers.fetch(),
        )

        # ----------------------------------------------------
        # News
        # ----------------------------------------------------

        articles = NewsAggregator(
            [
                YahooFinanceProvider(),
            ]
        ).fetch()

        articles = NewsClassifier.classify(
            articles,
        )

        articles = EntityExtractor.extract(
            articles,
        )

        articles = SectorMapper.map(
            articles,
        )

        articles = NewsScoringEngine.score(
            articles,
        )

        brief.top_news = NewsSummaryBuilder.build(
            articles,
            limit=5,
        )

        return self.health.calculate(
            brief,
        )