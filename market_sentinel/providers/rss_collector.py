"""
providers/rss_collector.py

Production-grade RSS Collector.

Downloads RSS/Atom feeds and converts them into NewsEvent objects.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterable

import feedparser
import requests
from loguru import logger

from market_sentinel.news.models import NewsEvent


class RSSCollector:
    """
    Collects news from multiple RSS feeds.
    """

    USER_AGENT = (
        "MarketSentinel/1.0 "
        "(https://marketsentinel.local)"
    )

    REQUEST_TIMEOUT = 15

    MAX_WORKERS = 8

    def __init__(
        self,
        feeds: Iterable[str],
    ) -> None:

        self._feeds = list(feeds)

    # ==========================================================
    # PUBLIC
    # ==========================================================

    def collect(self) -> list[NewsEvent]:
        """
        Download all configured RSS feeds.
        """

        logger.info(
            "Collecting {} RSS feeds...",
            len(self._feeds),
        )

        events: list[NewsEvent] = []

        with ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS,
        ) as executor:

            results = executor.map(
                self._collect_feed,
                self._feeds,
            )

            for articles in results:
                events.extend(articles)

        events = self._deduplicate(events)

        logger.info(
            "Collected {} unique article(s).",
            len(events),
        )

        return events

    # ==========================================================
    # INTERNAL
    # ==========================================================

    def _collect_feed(
        self,
        url: str,
    ) -> list[NewsEvent]:

        logger.info("Fetching {}", url)

        try:

            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={
                    "User-Agent": self.USER_AGENT,
                },
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content,
            )

            return self._parse_feed(feed)

        except Exception as exc:

            logger.exception(
                "Failed to fetch {} : {}",
                url,
                exc,
            )

            return []

    def _parse_feed(
        self,
        feed,
    ) -> list[NewsEvent]:

        articles: list[NewsEvent] = []

        source = ""

        if hasattr(feed, "feed"):
            source = feed.feed.get(
                "title",
                "RSS",
            )

        for entry in feed.entries:

            try:

                title = (
                    entry.get("title", "")
                    .strip()
                )

                url = entry.get(
                    "link",
                    "",
                ).strip()

                summary = (
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                ).strip()

                published = self._parse_date(
                    entry,
                )

                article = NewsEvent(
                    title=title,
                    source=source,
                    url=url,
                    published_at=published,
                    category="GENERAL",
                    subcategory="RSS",
                    summary=summary,
                    content="",
                    author=entry.get(
                        "author",
                        "",
                    ),
                    language="en",
                    tags=[],
                    provider="RSS",
                    provider_id=url,
                )

                articles.append(article)

            except Exception as exc:

                logger.exception(
                    "Skipping invalid RSS entry: {}",
                    exc,
                )

        return articles

    @staticmethod
    def _parse_date(
        entry,
    ) -> datetime:

        value = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("pubDate")
        )

        if not value:
            return datetime.utcnow()

        try:

            return parsedate_to_datetime(
                value,
            )

        except Exception:

            return datetime.utcnow()

    @staticmethod
    def _deduplicate(
        events: list[NewsEvent],
    ) -> list[NewsEvent]:

        unique = {}

        for event in events:

            if not event.url:
                continue

            unique[event.url] = event

        return list(unique.values())