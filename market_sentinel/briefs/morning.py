"""
briefs/morning.py

Production-grade Morning Brief Builder.

Responsibilities
----------------
- Collect Indian market indices.
- Collect sector data.
- Collect gainers / losers.
- Collect Indian-market news.
- Rank and diversify news.
- Select the most important news for the brief.
- Protect the brief from individual provider failures.
- Preserve a stable MorningBrief contract.
- Provide detailed operational logging.

Author  : Market Sentinel
Version : 3.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any, Callable

from loguru import logger

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

from market_sentinel.providers.news.indian_market_news import (
    IndianMarketNews,
)

from market_sentinel.providers.news.news_ranker import (
    NewsRanker,
)

from market_sentinel.providers.news.global_impact_news import (
    GlobalImpactNews,
)
from market_sentinel.providers.news.crypto_market_news import CryptoMarketNews
from market_sentinel.providers.external_markets import ExternalMarketsProvider
from market_sentinel.providers.nse_movers import NseMoversProvider
from market_sentinel.providers.premarket import PreMarketProvider
from market_sentinel.providers.sensex import SensexProvider
from market_sentinel.providers.us_movers import UsMarketMoversProvider

from market_sentinel.providers.market_brief_data import (
    InstitutionalFlowProvider,
    IpoGmpProvider,
)

from market_sentinel.briefs.ai_summary import (
    MarketSummaryGenerator,
)

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    # Number of news items internally retained by the brief.
    #
    # Formatter can display TOP 5 while the brief can retain
    # additional candidates for future use.
    NEWS_LIMIT = 8

    # Telegram's "TOP 5" should normally receive exactly five
    # high-quality stories when enough stories are available.
    DISPLAY_NEWS_LIMIT = 5

    # Do not allow very old articles into the primary morning
    # news selection.
    NEWS_MAX_AGE_HOURS = 36

    # Maximum number of stories from one source.
    #
    # Prevents the brief becoming:
    #
    #   Economic Times
    #   Economic Times
    #   Economic Times
    #   Economic Times
    #   Economic Times
    #
    SOURCE_DIVERSITY_LIMIT = 2

    # Maximum number of stories with the same / very similar title.
    TITLE_SIMILARITY_LIMIT = 1

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self) -> None:
        """
        Initialize all market and news providers.
        """

        logger.info(
            "Initializing MorningBriefBuilder v{}",
            self.VERSION,
        )

        self.indices = IndianIndicesProvider()

        self.sectors = SectorProvider()

        self.gainers = GainersProvider()

        self.losers = LosersProvider()

        self.health = MarketHealthEngine()

        # The briefing feed must be India-first.  The collector removes
        # irrelevant global/personal-finance stories; NewsRanker then scores,
        # clusters and diversifies the final event-level selection.
        self.news = IndianMarketNews()

        self.news_ranker = NewsRanker()

        self.global_news = GlobalImpactNews()
        self.crypto_news = CryptoMarketNews()
        self.external_markets = ExternalMarketsProvider()
        self.nse_movers = NseMoversProvider()
        self.premarket = PreMarketProvider()
        self.sensex = SensexProvider()
        self.us_movers = UsMarketMoversProvider()

        self.institutional_flows = InstitutionalFlowProvider()

        self.ipo_gmp = IpoGmpProvider()

        self.summary_generator = MarketSummaryGenerator()

    def build(self) -> MorningBrief:
        """
        Build the complete morning market brief.

        Provider failures are isolated wherever possible so that
        one failed external source does not destroy the complete
        morning report.
        """

        started_at = perf_counter()

        logger.info(
            "=================================================="
        )

        logger.info(
            "Starting Morning Brief build..."
        )

        # ------------------------------------------------------
        # Market data
        # ------------------------------------------------------

        indices = self._safe_fetch(
            name="Indian indices",
            provider=self.indices,
            fallback=[],
        )

        sectors = self._safe_fetch(
            name="Sector data",
            provider=self.sectors,
            fallback=[],
        )

        gainers = self._safe_fetch(
            name="Top gainers",
            provider=self.gainers,
            fallback=[],
        )

        losers = self._safe_fetch(
            name="Top losers",
            provider=self.losers,
            fallback=[],
        )

        # ------------------------------------------------------
        # News
        # ------------------------------------------------------

        top_news = self._build_news()

        # ------------------------------------------------------
        # Initial brief
        # ------------------------------------------------------

        generated_at = datetime.now(
            timezone.utc
        )

        brief = MorningBrief(
            generated_at=generated_at,

            health_score=0,

            market_sentiment="Unknown",

            confidence=0,

            top_news=top_news,

            indices=indices,

            sectors=sectors,

            gainers=self.nse_movers.fetch("gainers") or self.gainers.fetch(),

            losers=self.nse_movers.fetch("losers") or self.losers.fetch(),
        )

        # ------------------------------------------------------
        # Market health
        # ------------------------------------------------------

        brief = self._calculate_health(
            brief
        )

        elapsed = (
            perf_counter() - started_at
        )

        logger.info(
            "Morning Brief completed in {:.2f}s",
            elapsed,
        )

        logger.info(
            "News selected: {}",
            len(top_news),
        )

        logger.info(
            "=================================================="
        )

        return brief

    # ==========================================================
    # NEWS PIPELINE
    # ==========================================================

    def _build_news(self) -> list[Any]:
        """
        Execute the complete Indian-market news pipeline.

        Pipeline:

            collect
              ↓
            validate
              ↓
            freshness filter
              ↓
            URL/title deduplication
              ↓
            rank
              ↓
            source diversification
              ↓
            final selection
        """

        started_at = perf_counter()

        logger.info(
            "Starting Indian market news pipeline..."
        )

        # ------------------------------------------------------
        # Collect
        # ------------------------------------------------------

        raw_news = self._safe_collect_news()

        if not raw_news:
            logger.warning(
                "Indian news collector returned no articles."
            )

            return []

        logger.info(
            "Raw Indian news articles: {}",
            len(raw_news),
        )

        # ------------------------------------------------------
        # Validate
        # ------------------------------------------------------

        valid_news = [
            article
            for article in raw_news
            if self._is_valid_article(article)
        ]

        logger.info(
            "Valid news articles: {}",
            len(valid_news),
        )

        if not valid_news:
            return []

        # ------------------------------------------------------
        # Freshness
        # ------------------------------------------------------

        fresh_news = self._filter_fresh_news(
            valid_news
        )

        logger.info(
            "Fresh news articles: {}",
            len(fresh_news),
        )

        # If the feed contains no articles inside our freshness
        # window, don't completely lose the morning brief.
        #
        # Keep the valid articles as a fallback.
        candidates = (
            fresh_news
            if fresh_news
            else valid_news
        )

        # ------------------------------------------------------
        # Deduplication
        # ------------------------------------------------------

        unique_news = self._deduplicate_news(
            candidates
        )

        logger.info(
            "Unique news articles: {}",
            len(unique_news),
        )

        if not unique_news:
            return []

        # ------------------------------------------------------
        # Ranking
        # ------------------------------------------------------

        ranked_news = self._rank_news(
            unique_news
        )

        logger.info(
            "Ranked news articles: {}",
            len(ranked_news),
        )

        # ------------------------------------------------------
        # Diversification
        # ------------------------------------------------------

        diversified_news = (
            self._diversify_news(
                ranked_news
            )
        )

        # ------------------------------------------------------
        # Final selection
        # ------------------------------------------------------

        selected_news = diversified_news[
            : self.NEWS_LIMIT
        ]

        elapsed = (
            perf_counter() - started_at
        )

        logger.info(
            "Indian news pipeline completed in {:.2f}s",
            elapsed,
        )

        for index, article in enumerate(
            selected_news,
            start=1,
        ):
            title = self._article_title(
                article
            )

            score = self._article_score(
                article
            )

            source = self._article_source(
                article
            )

            logger.info(
                "NEWS #{} | score={} | source={} | {}",
                index,
                score,
                source,
                title,
            )

        return selected_news

    # ==========================================================
    # NEWS COLLECTION
    # ==========================================================

    def _safe_collect_news(self) -> list[Any]:
        """
        Collect news while protecting the morning pipeline from
        collector failures.
        """

        try:
            result = self.news.collect()

            if result is None:
                return []

            return list(result)

        except Exception as exc:
            logger.exception(
                "Indian market news collection failed: {}",
                exc,
            )

            return []

    # ==========================================================
    # NEWS RANKING
    # ==========================================================

    def _rank_news(
        self,
        articles: list[Any],
    ) -> list[Any]:
        """
        Rank news using the dedicated NewsRanker.

        The builder intentionally does not duplicate the ranking
        algorithm. NewsRanker remains the single owner of
        importance scoring.
        """

        try:
            ranked = self.news_ranker.rank(
                articles,
                limit=max(
                    self.NEWS_LIMIT * 3,
                    15,
                ),
            )

            return list(ranked or [])

        except Exception as exc:
            logger.exception(
                "News ranking failed: {}",
                exc,
            )

            # Graceful fallback:
            #
            # Keep the collected articles instead of producing
            # an empty brief.
            return sorted(
                articles,
                key=self._article_score,
                reverse=True,
            )

        brief.indian_news = self.news_ranker.rank(
            self.news.collect(),
            limit=5,
        )

        # Backwards compatibility for existing consumers that read top_news.
        brief.top_news = brief.indian_news

        brief.global_impact_news = self.global_news.collect(limit=5)
        brief.crypto_news = self.crypto_news.collect(limit=5)
        (
            brief.global_indices,
            brief.indian_adrs,
            brief.commodities,
            brief.crypto,
        ) = self.external_markets.fetch()
        brief.us_gainers = self.us_movers.fetch("gainers")
        brief.us_losers = self.us_movers.fetch("losers")

        brief.investor_flows = self.institutional_flows.fetch()

        brief.top_ipos = self.ipo_gmp.fetch_top(limit=10)
        brief.fo_ban_symbols = self.premarket.fetch_fo_ban()
        brief.fo_ban_available = self.premarket.fo_ban_available
        brief.gift_nifty = self.premarket.fetch_gift_nifty()

        if not any(item.name.upper() == "SENSEX" for item in brief.indices):
            sensex = self.sensex.fetch()
            if sensex:
                brief.indices.insert(1, sensex)

        brief.ai_summary, brief.ai_summary_source = (
            self.summary_generator.generate(brief)
        )

        return self.health.calculate(
            brief,
        )
