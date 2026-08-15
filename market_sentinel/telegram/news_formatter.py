"""
telegram/news_formatter.py

Production-grade Indian Market News Formatter.

Responsibilities
----------------
1. Format ranked Indian market news for Telegram.
2. Support NewsArticle and NewsAssessment objects.
3. Display market-impact score.
4. Display event classification.
5. Display detected entities/topics.
6. Display corroborating sources.
7. Display publication time.
8. Generate clickable Telegram links.
9. Escape Telegram HTML safely.
10. Keep formatting compact enough for Telegram.
11. Provide separate formats for:
      - Top market news
      - Breaking news
      - Compact news
      - Detailed intelligence
12. Never perform ranking or scoring itself.

Architecture
------------
RSS
 ↓
IndianMarketNews
 ↓
NewsRanker
 ↓
NewsPortfolioSelector
 ↓
NewsFormatter
 ↓
Telegram

Author  : Market Sentinel
Version : 2.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Iterable, Sequence

from market_sentinel.news.models import NewsArticle


class NewsFormatter:
    """
    Production-grade Telegram formatter for market news.

    This class is intentionally stateless.

    Ranking belongs to NewsRanker.
    Event selection belongs to NewsPortfolioSelector.
    Formatting belongs here.
    """

    VERSION = "2.0.0"

    # ==========================================================
    # TELEGRAM LIMITS
    # ==========================================================

    # Telegram messages can be much larger, but we keep the
    # news section compact so the entire market brief remains
    # readable.
    MAX_MESSAGE_LENGTH = 3900

    MAX_TITLE_LENGTH = 220
    MAX_SUMMARY_LENGTH = 320
    MAX_REASON_LENGTH = 180

    # ==========================================================
    # VISUAL CONSTANTS
    # ==========================================================

    LINE = "━━━━━━━━━━━━━━━━━━━━"

    SHORT_LINE = "────────────────────"

    # ==========================================================
    # SCORE LEVELS
    # ==========================================================

    SCORE_EXCEPTIONAL = 90
    SCORE_VERY_HIGH = 80
    SCORE_HIGH = 70
    SCORE_MODERATE = 55
    SCORE_LOW = 40

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    @classmethod
    def format_top_news(
        cls,
        assessments: Iterable,
        limit: int = 5,
        title: str = "🇮🇳 TOP 5 INDIAN MARKET NEWS",
    ) -> str:
        """
        Format selected NewsAssessment objects into a Telegram block.

        Parameters
        ----------
        assessments:
            Iterable of NewsAssessment objects.

        limit:
            Maximum number of stories.

        title:
            Section title.

        Returns
        -------
        str
            Telegram HTML formatted message.
        """

        items = list(assessments)[:limit]

        if not items:
            return (
                f"<b>{escape(title)}</b>\n"
                f"{cls.LINE}\n\n"
                "No important Indian market news found."
            )

        lines: list[str] = []

        lines.append(f"<b>{escape(title)}</b>")
        lines.append(cls.LINE)
        lines.append("")

        for index, assessment in enumerate(items, start=1):
            lines.extend(
                cls._format_assessment(
                    assessment,
                    index=index,
                    detailed=False,
                )
            )

            if index < len(items):
                lines.append("")

        return cls._finalize(lines)

    # ==========================================================
    # TOP MARKET NEWS
    # ==========================================================

    @classmethod
    def format_market_news(
        cls,
        articles: Iterable[NewsArticle],
        limit: int = 5,
        title: str = "📰 TOP MARKET NEWS",
    ) -> str:
        """
        Format plain NewsArticle objects.

        Useful when NewsPortfolioSelector is not being used.

        This method does NOT rank articles.
        """

        items = list(articles)[:limit]

        if not items:
            return (
                f"<b>{escape(title)}</b>\n"
                f"{cls.LINE}\n\n"
                "No market news available."
            )

        lines: list[str] = []

        lines.append(f"<b>{escape(title)}</b>")
        lines.append(cls.LINE)
        lines.append("")

        for index, article in enumerate(items, start=1):
            lines.extend(
                cls._format_article(
                    article,
                    index=index,
                    detailed=False,
                )
            )

            if index < len(items):
                lines.append("")

        return cls._finalize(lines)

    # ==========================================================
    # DETAILED INTELLIGENCE
    # ==========================================================

    @classmethod
    def format_intelligence(
        cls,
        assessment,
    ) -> str:
        """
        Format one NewsAssessment as a detailed intelligence card.

        Example
        -------
        🔥 HIGH IMPACT

        BofA to invest $1.9 billion...

        Impact Score : 91/100
        Event        : Corporate Action
        Entities     : Jio Financial
        Topics       : Equities, Banks

        Source       : Economic Times
        Corroborated : 2 sources

        Why selected:
        • Base importance 89/100
        • Classified as corporate action
        • Corroborated by 2 independent sources

        👉 Read full story
        """

        lines = cls._format_assessment(
            assessment,
            index=None,
            detailed=True,
        )

        return cls._finalize(lines)

    # ==========================================================
    # BREAKING NEWS
    # ==========================================================

    @classmethod
    def format_breaking(
        cls,
        assessment,
    ) -> str:
        """
        Format a single high-impact story as a breaking-news alert.
        """

        article = cls._get_article(assessment)

        score = cls._get_score(
            assessment,
            article,
        )

        impact_icon = cls._impact_icon(score)

        lines = [
            "🚨 <b>BREAKING MARKET NEWS</b>",
            cls.LINE,
            "",
            f"{impact_icon} <b>{cls._safe_title(article.title)}</b>",
            "",
            f"⚡ <b>Impact Score:</b> {score}/100",
        ]

        event_type = cls._get_event_type(assessment)

        if event_type:
            lines.append(
                f"🎯 <b>Event:</b> {cls._humanize(event_type)}"
            )

        if article.source:
            lines.append(
                f"📰 <b>Source:</b> {escape(article.source)}"
            )

        published = cls._format_time(
            article.published_at
        )

        if published:
            lines.append(
                f"🕒 <b>Published:</b> {published}"
            )

        lines.append("")

        if article.summary:
            lines.append(
                cls._truncate(
                    cls._clean_text(article.summary),
                    cls.MAX_SUMMARY_LENGTH,
                )
            )

        if article.url:
            lines.append("")
            lines.append(
                cls._read_more(article.url)
            )

        return cls._finalize(lines)

    # ==========================================================
    # COMPACT FORMAT
    # ==========================================================

    @classmethod
    def format_compact(
        cls,
        assessments: Iterable,
        limit: int = 5,
    ) -> str:
        """
        Compact format for Telegram messages where space is limited.
        """

        items = list(assessments)[:limit]

        if not items:
            return "📰 <b>INDIAN MARKET NEWS</b>\n\nNo important news."

        lines = [
            "🇮🇳 <b>INDIAN MARKET NEWS</b>",
            cls.LINE,
            "",
        ]

        for index, assessment in enumerate(items, start=1):

            article = cls._get_article(assessment)

            score = cls._get_score(
                assessment,
                article,
            )

            icon = cls._impact_icon(score)

            title = cls._safe_title(
                article.title,
                max_length=180,
            )

            source = escape(
                article.source or "Market News"
            )

            lines.append(
                f"{icon} <b>{index}. {title}</b>"
            )

            lines.append(
                f"   {cls._score_label(score)} "
                f"• {score}/100 • {source}"
            )

            if article.url:
                lines.append(
                    f'   <a href="{escape(article.url, quote=True)}">'
                    "Read More</a>"
                )

            lines.append("")

        return cls._finalize(lines)

    # ==========================================================
    # ASSESSMENT FORMATTER
    # ==========================================================

    @classmethod
    def _format_assessment(
        cls,
        assessment,
        index: int | None,
        detailed: bool,
    ) -> list[str]:

        article = cls._get_article(assessment)

        score = cls._get_score(
            assessment,
            article,
        )

        icon = cls._impact_icon(score)

        title = cls._safe_title(
            article.title
        )

        lines: list[str] = []

        # ------------------------------------------------------
        # TITLE
        # ------------------------------------------------------

        if index is not None:
            lines.append(
                f"{icon} <b>{index}. {title}</b>"
            )
        else:
            lines.append(
                f"{icon} <b>{title}</b>"
            )

        # ------------------------------------------------------
        # SCORE
        # ------------------------------------------------------

        lines.append(
            f"⚡ <b>Impact Score:</b> "
            f"{score}/100 "
            f"({cls._score_label(score)})"
        )

        # ------------------------------------------------------
        # EVENT
        # ------------------------------------------------------

        event_type = cls._get_event_type(
            assessment
        )

        if event_type:
            lines.append(
                f"🎯 <b>Event:</b> "
                f"{cls._humanize(event_type)}"
            )

        # ------------------------------------------------------
        # ENTITIES
        # ------------------------------------------------------

        entities = cls._get_tuple(
            assessment,
            "entities",
        )

        if entities:
            lines.append(
                "🏢 <b>Entities:</b> "
                + escape(
                    ", ".join(entities)
                )
            )

        # ------------------------------------------------------
        # TOPICS
        # ------------------------------------------------------

        topics = cls._get_tuple(
            assessment,
            "topics",
        )

        if topics:
            lines.append(
                "📌 <b>Topics:</b> "
                + escape(
                    ", ".join(
                        cls._humanize(topic)
                        for topic in topics
                    )
                )
            )

        # ------------------------------------------------------
        # SOURCE
        # ------------------------------------------------------

        if article.source:
            lines.append(
                f"📰 <b>Source:</b> "
                f"{escape(article.source)}"
            )

        # ------------------------------------------------------
        # CORROBORATION
        # ------------------------------------------------------

        sources = cls._get_tuple(
            assessment,
            "corroborating_sources",
        )

        cluster_size = getattr(
            assessment,
            "cluster_size",
            1,
        )

        if len(sources) > 1:
            lines.append(
                f"🔎 <b>Corroborated:</b> "
                f"{len(sources)} independent sources"
            )

            if detailed:
                lines.append(
                    "   "
                    + escape(
                        ", ".join(sources)
                    )
                )

        elif cluster_size > 1:
            lines.append(
                f"🔎 <b>Coverage:</b> "
                f"{cluster_size} articles"
            )

        # ------------------------------------------------------
        # PUBLICATION TIME
        # ------------------------------------------------------

        published = cls._format_time(
            article.published_at
        )

        if published:
            lines.append(
                f"🕒 <b>Published:</b> {published}"
            )

        # ------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------

        if detailed and article.summary:

            lines.append("")

            lines.append(
                "<b>Summary</b>"
            )

            lines.append(
                cls._truncate(
                    cls._clean_text(
                        article.summary
                    ),
                    cls.MAX_SUMMARY_LENGTH,
                )
            )

        # ------------------------------------------------------
        # SELECTION REASONS
        # ------------------------------------------------------

        if detailed:

            reasons = cls._get_tuple(
                assessment,
                "reasons",
            )

            if reasons:

                lines.append("")

                lines.append(
                    "<b>Why this matters</b>"
                )

                for reason in reasons[:4]:

                    clean_reason = cls._truncate(
                        cls._clean_text(reason),
                        cls.MAX_REASON_LENGTH,
                    )

                    lines.append(
                        f"• {escape(clean_reason)}"
                    )

        # ------------------------------------------------------
        # READ MORE
        # ------------------------------------------------------

        if article.url:

            lines.append("")

            lines.append(
                cls._read_more(
                    article.url
                )
            )

        return lines

    # ==========================================================
    # ARTICLE FORMATTER
    # ==========================================================

    @classmethod
    def _format_article(
        cls,
        article: NewsArticle,
        index: int | None,
        detailed: bool,
    ) -> list[str]:

        score = cls._normalise_score(
            getattr(
                article,
                "score",
                0,
            )
        )

        icon = cls._impact_icon(
            score
        )

        title = cls._safe_title(
            article.title
        )

        lines: list[str] = []

        # ------------------------------------------------------
        # TITLE
        # ------------------------------------------------------

        if index is not None:

            lines.append(
                f"{icon} <b>{index}. {title}</b>"
            )

        else:

            lines.append(
                f"{icon} <b>{title}</b>"
            )

        # ------------------------------------------------------
        # SCORE
        # ------------------------------------------------------

        lines.append(
            f"⚡ <b>Impact Score:</b> "
            f"{score}/100 "
            f"({cls._score_label(score)})"
        )

        # ------------------------------------------------------
        # SOURCE
        # ------------------------------------------------------

        if article.source:

            lines.append(
                f"📰 <b>Source:</b> "
                f"{escape(article.source)}"
            )

        # ------------------------------------------------------
        # PUBLISHED
        # ------------------------------------------------------

        published = cls._format_time(
            article.published_at
        )

        if published:

            lines.append(
                f"🕒 <b>Published:</b> "
                f"{published}"
            )

        # ------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------

        if detailed and article.summary:

            lines.append("")

            lines.append(
                cls._truncate(
                    cls._clean_text(
                        article.summary
                    ),
                    cls.MAX_SUMMARY_LENGTH,
                )
            )

        # ------------------------------------------------------
        # URL
        # ------------------------------------------------------

        if article.url:

            lines.append("")

            lines.append(
                cls._read_more(
                    article.url
                )
            )

        return lines

    # ==========================================================
    # SCORE HELPERS
    # ==========================================================

    @classmethod
    def _impact_icon(
        cls,
        score: int,
    ) -> str:

        score = cls._normalise_score(
            score
        )

        if score >= cls.SCORE_EXCEPTIONAL:
            return "🚨"

        if score >= cls.SCORE_VERY_HIGH:
            return "🔥"

        if score >= cls.SCORE_HIGH:
            return "🟠"

        if score >= cls.SCORE_MODERATE:
            return "🟡"

        return "⚪"

    @classmethod
    def _score_label(
        cls,
        score: int,
    ) -> str:

        score = cls._normalise_score(
            score
        )

        if score >= cls.SCORE_EXCEPTIONAL:
            return "EXCEPTIONAL"

        if score >= cls.SCORE_VERY_HIGH:
            return "VERY HIGH"

        if score >= cls.SCORE_HIGH:
            return "HIGH"

        if score >= cls.SCORE_MODERATE:
            return "MODERATE"

        if score >= cls.SCORE_LOW:
            return "LOW"

        return "VERY LOW"

    @staticmethod
    def _normalise_score(
        score,
    ) -> int:

        try:
            score = int(
                round(
                    float(score)
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            score = 0

        return max(
            0,
            min(
                score,
                100,
            ),
        )

    # ==========================================================
    # ASSESSMENT HELPERS
    # ==========================================================

    @staticmethod
    def _get_article(
        assessment,
    ) -> NewsArticle:

        if isinstance(
            assessment,
            NewsArticle,
        ):
            return assessment

        article = getattr(
            assessment,
            "article",
            None,
        )

        if article is None:
            raise TypeError(
                "Expected NewsArticle or "
                "NewsAssessment-like object."
            )

        return article

    @classmethod
    def _get_score(
        cls,
        assessment,
        article: NewsArticle,
    ) -> int:

        # Base NewsRanker score is the authoritative
        # market importance score.

        score = getattr(
            article,
            "score",
            None,
        )

        if score is not None:
            return cls._normalise_score(
                score
            )

        # Fallback for custom assessment objects.
        score = getattr(
            assessment,
            "selection_score",
            0,
        )

        return cls._normalise_score(
            score
        )

    @staticmethod
    def _get_event_type(
        assessment,
    ) -> str:

        if assessment is None:
            return ""

        return str(
            getattr(
                assessment,
                "event_type",
                "",
            )
            or ""
        )

    @staticmethod
    def _get_tuple(
        assessment,
        attribute: str,
    ) -> tuple[str, ...]:

        if assessment is None:
            return ()

        value = getattr(
            assessment,
            attribute,
            (),
        )

        if not value:
            return ()

        return tuple(
            str(item)
            for item in value
            if item
        )

    # ==========================================================
    # TEXT HELPERS
    # ==========================================================

    @staticmethod
    def _safe_title(
        title: str | None,
        max_length: int = 220,
    ) -> str:

        title = (
            title
            or "Untitled market story"
        )

        title = NewsFormatter._clean_text(
            title
        )

        title = NewsFormatter._truncate(
            title,
            max_length,
        )

        return escape(
            title
        )

    @staticmethod
    def _clean_text(
        text: str | None,
    ) -> str:

        if not text:
            return ""

        # Remove excessive whitespace.
        text = " ".join(
            str(text).split()
        )

        return text.strip()

    @staticmethod
    def _truncate(
        text: str,
        max_length: int,
    ) -> str:

        text = text or ""

        if len(text) <= max_length:
            return text

        return (
            text[: max_length - 1]
            .rstrip()
            + "…"
        )

    @staticmethod
    def _humanize(
        value: str,
    ) -> str:

        if not value:
            return ""

        value = str(
            value
        ).replace(
            "_",
            " ",
        )

        return value.title()

    # ==========================================================
    # DATE / TIME
    # ==========================================================

    @staticmethod
    def _format_time(
        published_at: datetime | None,
    ) -> str:

        if published_at is None:
            return ""

        try:

            if published_at.tzinfo is None:

                published_at = published_at.replace(
                    tzinfo=timezone.utc
                )

            # Convert to IST.
            from datetime import timedelta

            ist = timezone(
                timedelta(
                    hours=5,
                    minutes=30,
                )
            )

            published_at = published_at.astimezone(
                ist
            )

            return published_at.strftime(
                "%d %b %Y | %I:%M %p IST"
            )

        except (
            AttributeError,
            ValueError,
            TypeError,
        ):

            return ""

    # ==========================================================
    # URL
    # ==========================================================

    @staticmethod
    def _read_more(
        url: str,
    ) -> str:

        if not url:
            return ""

        safe_url = escape(
            str(url),
            quote=True,
        )

        return (
            f'👉 <a href="{safe_url}">'
            "Read Full Story</a>"
        )

    # ==========================================================
    # MESSAGE FINALIZER
    # ==========================================================

    @classmethod
    def _finalize(
        cls,
        lines: Sequence[str],
    ) -> str:

        message = "\n".join(
            lines
        ).strip()

        if len(message) <= cls.MAX_MESSAGE_LENGTH:
            return message

        # Never cut HTML in the middle.
        # Instead remove complete lines from the end.
        safe_lines = list(lines)

        while (
            safe_lines
            and len(
                "\n".join(
                    safe_lines
                )
            ) > cls.MAX_MESSAGE_LENGTH
        ):
            safe_lines.pop()

        message = "\n".join(
            safe_lines
        ).strip()

        return message