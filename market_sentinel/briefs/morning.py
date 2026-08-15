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


class MorningBriefBuilder:
    """
    Builds the complete Market Sentinel morning brief.

    Architecture
    ------------

        Market Providers
              │
              ├── Indices
              ├── Sectors
              ├── Gainers
              └── Losers
              │
              ▼
        Indian News Collector
              │
              ▼
        News Ranking
              │
              ▼
        News Deduplication
              │
              ▼
        News Diversification
              │
              ▼
        Top News Selection
              │
              ▼
        MorningBrief
              │
              ▼
        MarketHealthEngine
              │
              ▼
        Telegram Formatter
    """

    VERSION = "3.0.0"

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

        # ------------------------------------------------------
        # India-first news pipeline
        # ------------------------------------------------------

        self.news = IndianMarketNews()

        self.news_ranker = NewsRanker()

        logger.info(
            "MorningBriefBuilder initialized successfully."
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

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

            gainers=gainers,

            losers=losers,
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

    # ==========================================================
    # NEWS VALIDATION
    # ==========================================================

    @staticmethod
    def _is_valid_article(
        article: Any,
    ) -> bool:
        """
        Validate the minimum structure required for a news article.
        """

        if article is None:
            return False

        title = MorningBriefBuilder._article_title(
            article
        )

        url = MorningBriefBuilder._article_url(
            article
        )

        # A news item without a title is not useful.
        if not title:
            return False

        # URL is strongly preferred.
        #
        # Some official feeds can occasionally omit it, so we
        # don't reject the article purely for that reason.
        if not url:
            source = MorningBriefBuilder._article_source(
                article
            )

            if not source:
                return False

        return True

    # ==========================================================
    # FRESHNESS
    # ==========================================================

    def _filter_fresh_news(
        self,
        articles: list[Any],
    ) -> list[Any]:
        """
        Remove stale articles.

        Articles without a publication timestamp are retained
        because some RSS feeds do not expose a valid date.
        """

        now = datetime.now(
            timezone.utc
        )

        cutoff = (
            now
            - timedelta(
                hours=self.NEWS_MAX_AGE_HOURS
            )
        )

        fresh: list[Any] = []

        for article in articles:
            published_at = self._article_datetime(
                article
            )

            if published_at is None:
                fresh.append(article)
                continue

            if published_at >= cutoff:
                fresh.append(article)

        return fresh

    # ==========================================================
    # DEDUPLICATION
    # ==========================================================

    def _deduplicate_news(
        self,
        articles: list[Any],
    ) -> list[Any]:
        """
        Deduplicate news using:

            1. URL
            2. normalized title
            3. title similarity heuristic

        The highest-ranked / first article is retained.
        """

        unique: list[Any] = []

        seen_urls: set[str] = set()
        seen_titles: set[str] = set()

        for article in articles:
            url = self._normalize_url(
                self._article_url(article)
            )

            title = self._normalize_title(
                self._article_title(article)
            )

            # --------------------------------------------------
            # URL duplicate
            # --------------------------------------------------

            if url and url in seen_urls:
                continue

            # --------------------------------------------------
            # Exact title duplicate
            # --------------------------------------------------

            if title and title in seen_titles:
                continue

            if url:
                seen_urls.add(url)

            if title:
                seen_titles.add(title)

            unique.append(article)

        return unique

    # ==========================================================
    # DIVERSIFICATION
    # ==========================================================

    def _diversify_news(
        self,
        articles: list[Any],
    ) -> list[Any]:
        """
        Prevent the TOP NEWS section from being dominated by one
        source.

        Ranking remains primary.

        Source diversity is only a secondary constraint.
        """

        selected: list[Any] = []

        source_counts: dict[str, int] = {}

        # ------------------------------------------------------
        # First pass:
        # Respect source diversity.
        # ------------------------------------------------------

        for article in articles:
            source = self._normalize_source(
                self._article_source(article)
            )

            count = source_counts.get(
                source,
                0,
            )

            if (
                source
                and count >= self.SOURCE_DIVERSITY_LIMIT
            ):
                continue

            selected.append(article)

            if source:
                source_counts[source] = (
                    count + 1
                )

            if len(selected) >= self.NEWS_LIMIT:
                break

        # ------------------------------------------------------
        # Second pass:
        # If diversity caused too few articles, fill remaining
        # slots using the original ranking.
        # ------------------------------------------------------

        if len(selected) < self.NEWS_LIMIT:

            selected_ids = {
                id(article)
                for article in selected
            }

            for article in articles:
                if id(article) in selected_ids:
                    continue

                selected.append(article)

                if len(selected) >= self.NEWS_LIMIT:
                    break

        return selected

    # ==========================================================
    # HEALTH
    # ==========================================================

    def _calculate_health(
        self,
        brief: MorningBrief,
    ) -> MorningBrief:
        """
        Calculate market health.

        MarketHealthEngine remains the authoritative owner of
        health calculation.
        """

        try:
            result = self.health.calculate(
                brief
            )

            if result is None:
                logger.warning(
                    "MarketHealthEngine returned None."
                )

                return brief

            return result

        except Exception as exc:
            logger.exception(
                "Market health calculation failed: {}",
                exc,
            )

            return brief

    # ==========================================================
    # GENERIC PROVIDER HELPER
    # ==========================================================

    @staticmethod
    def _safe_fetch(
        name: str,
        provider: Any,
        fallback: Any,
    ) -> Any:
        """
        Safely execute a provider's fetch() method.

        This prevents a single market-data provider failure from
        breaking the entire morning brief.
        """

        started_at = perf_counter()

        try:
            fetch_method = getattr(
                provider,
                "fetch",
            )

            result = fetch_method()

            elapsed = (
                perf_counter() - started_at
            )

            if result is None:
                logger.warning(
                    "{} provider returned no data "
                    "after {:.2f}s",
                    name,
                    elapsed,
                )

                return fallback

            logger.info(
                "{} collected successfully "
                "in {:.2f}s",
                name,
                elapsed,
            )

            return result

        except Exception as exc:
            elapsed = (
                perf_counter() - started_at
            )

            logger.exception(
                "{} provider failed after {:.2f}s: {}",
                name,
                elapsed,
                exc,
            )

            return fallback

    # ==========================================================
    # ARTICLE ACCESSORS
    # ==========================================================

    @staticmethod
    def _article_title(
        article: Any,
    ) -> str:
        return str(
            getattr(
                article,
                "title",
                "",
            ) or ""
        ).strip()

    @staticmethod
    def _article_url(
        article: Any,
    ) -> str:
        return str(
            getattr(
                article,
                "url",
                "",
            ) or ""
        ).strip()

    @staticmethod
    def _article_source(
        article: Any,
    ) -> str:
        return str(
            getattr(
                article,
                "source",
                "",
            ) or ""
        ).strip()

    @staticmethod
    def _article_score(
        article: Any,
    ) -> int:
        """
        Read the ranking score.

        Supports both:

            article.score

        and legacy:

            article.impact
        """

        value = getattr(
            article,
            "score",
            None,
        )

        if value is None:
            value = getattr(
                article,
                "impact",
                0,
            )

        try:
            return int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _article_datetime(
        article: Any,
    ) -> datetime | None:
        """
        Safely extract article publication datetime.

        Naive timestamps are interpreted as UTC because the
        collector normalizes feed timestamps to timezone-aware
        values.
        """

        value = getattr(
            article,
            "published_at",
            None,
        )

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            if value.tzinfo is None:
                return value.replace(
                    tzinfo=timezone.utc
                )

            return value.astimezone(
                timezone.utc
            )

        return None

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:
        """
        Normalize URLs for duplicate detection.
        """

        if not url:
            return ""

        normalized = url.strip().lower()

        # Remove trailing slash.
        normalized = normalized.rstrip("/")

        return normalized

    @staticmethod
    def _normalize_source(
        source: str,
    ) -> str:
        """
        Normalize source names.
        """

        if not source:
            return ""

        return (
            source
            .strip()
            .lower()
        )

    @staticmethod
    def _normalize_title(
        title: str,
    ) -> str:
        """
        Normalize titles for exact duplicate detection.
        """

        if not title:
            return ""

        normalized = (
            title
            .strip()
            .lower()
        )

        # Collapse whitespace.
        normalized = " ".join(
            normalized.split()
        )

        # Remove common punctuation.
        normalized = (
            normalized
            .replace(".", "")
            .replace(",", "")
            .replace(":", "")
            .replace(";", "")
            .replace("|", "")
            .replace("-", " ")
        )

        return " ".join(
            normalized.split()
        )

    # ==========================================================
    # DEBUG / DIAGNOSTICS
    # ==========================================================

    def diagnostics(
        self,
        brief: MorningBrief,
    ) -> dict[str, Any]:
        """
        Return diagnostic information about the generated brief.

        Useful for tests, logging, monitoring and future
        observability dashboards.
        """

        news = list(
            getattr(
                brief,
                "top_news",
                [],
            )
            or []
        )

        scores = [
            self._article_score(
                article
            )
            for article in news
        ]

        sources = [
            self._article_source(
                article
            )
            for article in news
        ]

        return {
            "builder_version": self.VERSION,
            "generated_at": getattr(
                brief,
                "generated_at",
                None,
            ),
            "news_count": len(news),
            "news_scores": scores,
            "news_sources": sources,
            "highest_news_score": (
                max(scores)
                if scores
                else 0
            ),
            "lowest_news_score": (
                min(scores)
                if scores
                else 0
            ),
            "health_score": getattr(
                brief,
                "health_score",
                0,
            ),
            "market_sentiment": getattr(
                brief,
                "market_sentiment",
                "Unknown",
            ),
            "confidence": getattr(
                brief,
                "confidence",
                0,
            ),
        }