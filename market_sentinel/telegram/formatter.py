"""
market_sentinel/telegram/formatter.py

Production-grade Telegram broadcast formatter for Market Sentinel.

Responsibilities
----------------
- Format MorningBrief objects into Telegram HTML.
- Format Indian / global market data.
- Format commodities.
- Format catalysts.
- Format stocks to watch.
- Format risks.
- Format market playbook.
- Format TOP 5 INDIAN MARKET NEWS.
- Safely handle optional / missing fields.
- Escape Telegram HTML-sensitive characters.
- Prevent malformed Telegram messages.
- Keep output compact and readable on mobile.

Author  : Market Sentinel
Version : 3.0.0
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Iterable


class BroadcastFormatter:
    """
    Production formatter for Market Sentinel Telegram broadcasts.

    Telegram parse mode:
        HTML

    All dynamic text is escaped before being inserted into
    the Telegram message.
    """

    VERSION = "3.0.0"

    # ==========================================================
    # VISUAL CONSTANTS
    # ==========================================================

    LINE = "━━━━━━━━━━━━━━━━━━━━━━"
    SHORT_LINE = "──────────────────────"

    FOOTER = "⚡ <i>Market Wavez Analytics</i>"

    MAX_NEWS_ITEMS = 5
    MAX_CATALYSTS = 5
    MAX_STOCKS = 10
    MAX_RISKS = 10

    MAX_TITLE_LENGTH = 180
    MAX_SUMMARY_LENGTH = 240
    MAX_REASON_LENGTH = 180
    MAX_PLAYBOOK_LENGTH = 800

    # ==========================================================
    # BASIC HELPERS
    # ==========================================================

    @staticmethod
    def _text(value: Any, default: str = "") -> str:
        """
        Convert a value into safe string text.
        """

        if value is None:
            return default

        return str(value).strip()

    @staticmethod
    def _escape(value: Any, default: str = "") -> str:
        """
        Escape dynamic content for Telegram HTML.
        """

        text = BroadcastFormatter._text(
            value,
            default=default,
        )

        return escape(
            text,
            quote=False,
        )

    @staticmethod
    def _truncate(
        value: Any,
        limit: int,
        suffix: str = "…",
    ) -> str:
        """
        Truncate text without producing excessively long
        Telegram messages.
        """

        text = BroadcastFormatter._text(value)

        if len(text) <= limit:
            return text

        return text[: max(0, limit - len(suffix))].rstrip() + suffix

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """
        Safely convert numeric values to float.
        """

        try:
            if value is None:
                return default

            return float(value)

        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        """
        Safely convert numeric values to int.
        """

        try:
            if value is None:
                return default

            return int(value)

        except (TypeError, ValueError):
            return default

    @staticmethod
    def _items(
        value: Any,
    ) -> list[Any]:
        """
        Safely convert iterable-like values into a list.
        """

        if value is None:
            return []

        if isinstance(value, (str, bytes)):
            return []

        try:
            return list(value)

        except TypeError:
            return []

    # ==========================================================
    # MARKET INDICATORS
    # ==========================================================

    @staticmethod
    def _emoji(change: float) -> str:
        """
        Direction emoji.
        """

        if change > 0:
            return "🟢"

        if change < 0:
            return "🔴"

        return "🟡"

    @staticmethod
    def _arrow(change: float) -> str:
        """
        Direction arrow.
        """

        if change > 0:
            return "▲"

        if change < 0:
            return "▼"

        return "■"

    @staticmethod
    def _change_text(change: float) -> str:
        """
        Format percentage change.
        """

        return f"{change:+.2f}%"

        lines.append(cls.LINE)
        lines.append("🌍 <b>DAILY MARKET BRIEF</b>")
        lines.append(f"📅 {brief.generated_at}")
        lines.append(cls.LINE)
        lines.append("")

        score = max(
            0,
            min(
                100,
                score,
            ),
        )

        if score >= 85:
            return "🟢 Exceptional"

        if score >= 75:
            return "🟢 Strong"

        if score >= 65:
            return "🟢 Healthy"

        if score >= 50:
            return "🟡 Neutral"

        if score >= 35:
            return "🟠 Weak"

        if score >= 20:
            return "🔴 Poor"

        return "🔴 Critical"

    # ==========================================================
    # NEWS HELPERS
    # ==========================================================

    @staticmethod
    def _news_score_label(score: int) -> str:
        """
        Convert news impact score into a classification.
        """

        score = max(
            0,
            min(
                100,
                score,
            ),
        )

        if score >= 90:
            return "🚨 EXCEPTIONAL"

        if score >= 80:
            return "🔥 VERY HIGH"

        if score >= 70:
            return "⚡ HIGH"

        if score >= 55:
            return "🟡 MODERATE"

        if score >= 40:
            return "🔵 LOW"

        return "⚪ MINOR"

    @staticmethod
    def _news_event_icon(article: Any) -> str:
        """
        Select an icon based on article characteristics.

        This intentionally uses getattr() so the formatter remains
        compatible with different NewsArticle versions.
        """

        category = BroadcastFormatter._text(
            getattr(article, "category", "")
        ).lower()

        title = BroadcastFormatter._text(
            getattr(article, "title", "")
        ).lower()

        text = f"{category} {title}"

        if any(
            keyword in text
            for keyword in (
                "result",
                "earnings",
                "profit",
                "revenue",
            )
        ):
            return "📊"

        if any(
            keyword in text
            for keyword in (
                "rbi",
                "rate cut",
                "rate hike",
                "inflation",
                "gdp",
                "policy",
            )
        ):
            return "🏦"

        if any(
            keyword in text
            for keyword in (
                "acquisition",
                "merger",
                "stake",
                "buyback",
                "dividend",
                "fundraise",
            )
        ):
            return "💰"

        if any(
            keyword in text
            for keyword in (
                "order",
                "contract",
                "deal",
                "partnership",
            )
        ):
            return "📦"

        if any(
            keyword in text
            for keyword in (
                "sebi",
                "regulation",
                "regulatory",
            )
        ):
            return "⚖️"

        return "📰"

    @staticmethod
    def _format_published_at(
        published_at: Any,
    ) -> str:
        """
        Format publication timestamp.

        The news pipeline is expected to normalize timestamps.
        This method intentionally avoids changing timezone semantics.
        """

        if published_at is None:
            return ""

        try:
            if isinstance(
                published_at,
                datetime,
            ):
                return published_at.strftime(
                    "%d %b %Y | %I:%M %p"
                )

            return BroadcastFormatter._text(
                published_at
            )

        except Exception:
            return ""

    @staticmethod
    def _news_url(article: Any) -> str:
        """
        Return article URL.
        """

        return BroadcastFormatter._text(
            getattr(
                article,
                "url",
                "",
            )
        )

    # ==========================================================
    # TOP NEWS
    # ==========================================================

    @classmethod
    def _format_top_news(
        cls,
        news: Iterable[Any] | None,
    ) -> list[str]:
        """
        Format TOP 5 INDIAN MARKET NEWS.

        Supports NewsArticle fields such as:

            title
            summary
            source
            url
            published_at
            score
            impact
            sentiment
            category
            entities
            sectors
            symbols
            duplicate
        """

        articles = cls._items(news)

        lines: list[str] = []

        lines.append(
            "🇮🇳 <b>TOP 5 INDIAN MARKET NEWS</b>"
        )
        lines.append(cls.LINE)
        lines.append("")

        if not articles:
            lines.append(
                "ℹ️ No significant Indian market news detected."
            )
            return lines

        # ------------------------------------------------------
        # Limit to top 5
        # ------------------------------------------------------

        articles = articles[: cls.MAX_NEWS_ITEMS]

        for index, article in enumerate(
            articles,
            start=1,
        ):
            title = cls._truncate(
                getattr(
                    article,
                    "title",
                    "Untitled",
                ),
                cls.MAX_TITLE_LENGTH,
            )

            source = cls._text(
                getattr(
                    article,
                    "source",
                    "Unknown Source",
                ),
                "Unknown Source",
            )

            url = cls._news_url(article)

            score = cls._safe_int(
                getattr(
                    article,
                    "score",
                    getattr(
                        article,
                        "impact",
                        0,
                    ),
                )
            )

            score = max(
                0,
                min(
                    100,
                    score,
                ),
            )

            sentiment = cls._text(
                getattr(
                    article,
                    "sentiment",
                    "Neutral",
                ),
                "Neutral",
            )

            category = cls._text(
                getattr(
                    article,
                    "category",
                    "",
                )
            )

            summary = cls._truncate(
                getattr(
                    article,
                    "summary",
                    "",
                ),
                cls.MAX_SUMMARY_LENGTH,
            )

            entities = cls._items(
                getattr(
                    article,
                    "entities",
                    None,
                )
            )

            sectors = cls._items(
                getattr(
                    article,
                    "sectors",
                    None,
                )
            )

            published = cls._format_published_at(
                getattr(
                    article,
                    "published_at",
                    None,
                )
            )

            # --------------------------------------------------
            # Header
            # --------------------------------------------------

            icon = cls._news_event_icon(
                article
            )

            lines.append(
                f"{icon} <b>{index}. "
                f"{cls._escape(title)}</b>"
            )

            # --------------------------------------------------
            # Score
            # --------------------------------------------------

            lines.append(
                f"⚡ <b>Impact Score:</b> "
                f"{score}/100 "
                f"{cls._news_score_label(score)}"
            )

            # --------------------------------------------------
            # Sentiment
            # --------------------------------------------------

            if sentiment:
                sentiment_lower = sentiment.lower()

                if "positive" in sentiment_lower:
                    sentiment_icon = "🟢"

                elif "negative" in sentiment_lower:
                    sentiment_icon = "🔴"

                else:
                    sentiment_icon = "🟡"

                lines.append(
                    f"{sentiment_icon} "
                    f"<b>Sentiment:</b> "
                    f"{cls._escape(sentiment)}"
                )

            # --------------------------------------------------
            # Event
            # --------------------------------------------------

            if category:
                lines.append(
                    f"🎯 <b>Event:</b> "
                    f"{cls._escape(category)}"
                )

            # --------------------------------------------------
            # Entities
            # --------------------------------------------------

            if entities:
                entity_text = ", ".join(
                    cls._text(entity)
                    for entity in entities[:5]
                    if cls._text(entity)
                )

                if entity_text:
                    lines.append(
                        f"🏢 <b>Entities:</b> "
                        f"{cls._escape(entity_text)}"
                    )

            # --------------------------------------------------
            # Sectors
            # --------------------------------------------------

            if sectors:
                sector_text = ", ".join(
                    cls._text(sector)
                    for sector in sectors[:5]
                    if cls._text(sector)
                )

                if sector_text:
                    lines.append(
                        f"📌 <b>Sectors:</b> "
                        f"{cls._escape(sector_text)}"
                    )

            # --------------------------------------------------
            # Summary
            # --------------------------------------------------

            if summary:
                lines.append(
                    f"📝 {cls._escape(summary)}"
                )

            # --------------------------------------------------
            # Source
            # --------------------------------------------------

            lines.append(
                f"📰 <b>Source:</b> "
                f"{cls._escape(source)}"
            )

            # --------------------------------------------------
            # Published
            # --------------------------------------------------

            if published:
                lines.append(
                    f"🕒 <b>Published:</b> "
                    f"{cls._escape(published)}"
                )

            # --------------------------------------------------
            # Read story
            # --------------------------------------------------

            if url:
                safe_url = cls._escape(
                    url
                )

                lines.append(
                    f'👉 <a href="{safe_url}">'
                    f"Read Full Story</a>"
                )

            lines.append("")

            if index < len(articles):
                lines.append(
                    cls.SHORT_LINE
                )
                lines.append("")

        return lines

    # ==========================================================
    # MARKET SECTION
    # ==========================================================

    @classmethod
    def _format_market_section(
        cls,
        title: str,
        markets: Iterable[Any] | None,
        flag: str,
    ) -> list[str]:
        """
        Format an index/market section.
        """

        lines: list[str] = []

        lines.append(cls.LINE)
        lines.append(
            f"{flag} <b>{cls._escape(title)}</b>"
        )
        lines.append(cls.LINE)

        markets = cls._items(markets)

        if not markets:
            lines.append(
                "ℹ️ No market data available."
            )
            return lines

        for market in markets:
            name = cls._text(
                getattr(
                    market,
                    "name",
                    "Unknown",
                ),
                "Unknown",
            )

            value = cls._safe_float(
                getattr(
                    market,
                    "value",
                    0,
                )
            )

            change = cls._safe_float(
                getattr(
                    market,
                    "change_percent",
                    0,
                )
            )

            emoji = cls._emoji(change)
            arrow = cls._arrow(change)

            line = (
                f"{emoji} <b>{cls._escape(name)}</b> "
                f"{value:,.2f} "
                f"| {arrow} "
                f"{change:+.2f}%"
            )

            volume = getattr(
                market,
                "volume",
                None,
            )

            if volume is not None:
                volume_value = cls._safe_float(
                    volume,
                    default=0,
                )

                if volume_value > 1:
                    line += (
                        f" "
                        f"📊 {volume_value:.2f}x"
                    )

            lines.append(line)

        return lines

    # ==========================================================
    # CATALYSTS
    # ==========================================================

    @classmethod
    def _format_catalysts(
        cls,
        catalysts: Iterable[Any] | None,
    ) -> list[str]:
        """
        Format market catalysts.
        """

        lines = [
            "🔥 <b>TOP CATALYSTS TODAY</b>",
            "",
        ]

        catalysts = cls._items(
            catalysts
        )[: cls.MAX_CATALYSTS]

        if not catalysts:
            lines.append(
                "ℹ️ No major catalysts identified."
            )
            return lines

        for index, catalyst in enumerate(
            catalysts,
            start=1,
        ):
            title = cls._escape(
                cls._truncate(
                    getattr(
                        catalyst,
                        "title",
                        "Market catalyst",
                    ),
                    cls.MAX_TITLE_LENGTH,
                )
            )

            impact = cls._escape(
                getattr(
                    catalyst,
                    "impact",
                    "",
                )
            )

            lines.append(
                f"<b>{index}. {title}</b>"
            )

            if impact:
                lines.append(
                    f"↳ {impact}"
                )

            lines.append("")

        return lines

    # ==========================================================
    # COMMODITIES
    # ==========================================================

    @classmethod
    def _format_commodities(
        cls,
        commodities: Iterable[Any] | None,
    ) -> list[str]:
        """
        Format commodity section.
        """

        lines = [
            "",
            cls.LINE,
            "🛢️ <b>COMMODITIES</b>",
            cls.LINE,
        ]

        commodities = cls._items(
            commodities
        )

        if not commodities:
            lines.append(
                "ℹ️ No commodity data available."
            )
            return lines

        for item in commodities:
            name = cls._escape(
                getattr(
                    item,
                    "name",
                    "Commodity",
                )
            )

            change = cls._safe_float(
                getattr(
                    item,
                    "change_percent",
                    0,
                )
            )

            comment = cls._escape(
                getattr(
                    item,
                    "comment",
                    "",
                )
            )

            emoji = cls._emoji(
                change
            )

            line = (
                f"{emoji} <b>{name}</b>: "
                f"{change:+.2f}%"
            )

            if comment:
                line += (
                    f" "
                    f"({comment})"
                )

            lines.append(line)

        return lines

    # ==========================================================
    # STOCK RADAR
    # ==========================================================

    @classmethod
    def _format_stocks_to_watch(
        cls,
        stocks: Iterable[Any] | None,
    ) -> list[str]:
        """
        Format stock watchlist.
        """

        lines = [
            "👀 <b>STOCKS TO WATCH</b>",
            "",
        ]

        stocks = cls._items(
            stocks
        )[: cls.MAX_STOCKS]

        if not stocks:
            lines.append(
                "ℹ️ No stocks identified."
            )
            return lines

        for stock in stocks:
            symbol = cls._escape(
                getattr(
                    stock,
                    "symbol",
                    "N/A",
                )
            )

            reason = cls._truncate(
                getattr(
                    stock,
                    "reason",
                    "",
                ),
                cls.MAX_REASON_LENGTH,
            )

            lines.append(
                f"🎯 <b>{symbol}</b>"
            )

            if reason:
                lines.append(
                    f"   ↳ {cls._escape(reason)}"
                )

        return lines

    # ==========================================================
    # RISKS
    # ==========================================================

    @classmethod
    def _format_risks(
        cls,
        risks: Iterable[Any] | None,
    ) -> list[str]:
        """
        Format market risks.
        """

        lines = [
            "",
            "⚠️ <b>KEY RISKS</b>",
            "",
        ]

        risks = cls._items(
            risks
        )[: cls.MAX_RISKS]

        if not risks:
            lines.append(
                "🟢 No major risks detected."
            )
            return lines

        for risk in risks:
            description = cls._truncate(
                getattr(
                    risk,
                    "description",
                    "Market risk detected.",
                ),
                cls.MAX_REASON_LENGTH,
            )

            lines.append(
                f"⚠️ {cls._escape(description)}"
            )

        return lines

    # ==========================================================
    # MAIN MORNING BROADCAST
    # ==========================================================

    @classmethod
    def morning(
        cls,
        brief: Any,
    ) -> str:
        """
        Build complete Market Sentinel morning broadcast.

        The method is intentionally defensive and uses getattr()
        for optional sections so one missing data provider does
        not break the entire Telegram broadcast.
        """

        lines: list[str] = []

        # ======================================================
        # HEADER
        # ======================================================

        lines.append(cls.LINE)
        lines.append(
            "🌍 <b>MARKET WAVES</b>"
        )
        lines.append(
            "📊 <b>DAILY MARKET BRIEF</b>"
        )
        lines.append(cls.LINE)
        lines.append("")

        generated_at = cls._text(
            getattr(
                brief,
                "generated_at",
                "",
            )
        )

        if generated_at:
            lines.append(
                f"📅 {cls._escape(generated_at)}"
            )
            lines.append("")

        # ======================================================
        # MARKET HEALTH
        # ======================================================

        health_score = cls._safe_int(
            getattr(
                brief,
                "market_health_score",
                0,
            )
        )

        health_status = cls._health(
            health_score
        )

        lines.append(
            f"❤️ <b>MARKET HEALTH</b>"
        )

        lines.append(
            f"{health_status} "
            f"<b>{health_score}/100</b>"
        )

        overall_sentiment = cls._text(
            getattr(
                brief,
                "overall_sentiment",
                "",
            )
        )

        if overall_sentiment:
            lines.append(
                f"🧠 <b>Overall Sentiment:</b> "
                f"{cls._escape(overall_sentiment)}"
            )

        india_sentiment = cls._text(
            getattr(
                brief,
                "india_sentiment",
                "",
            )
        )

        us_sentiment = cls._text(
            getattr(
                brief,
                "us_sentiment",
                "",
            )
        )

        crypto_sentiment = cls._text(
            getattr(
                brief,
                "crypto_sentiment",
                "",
            )
        )

        sentiment_parts = []

        if india_sentiment:
            sentiment_parts.append(
                f"🇮🇳 {cls._escape(india_sentiment)}"
            )

        if us_sentiment:
            sentiment_parts.append(
                f"🇺🇸 {cls._escape(us_sentiment)}"
            )

        if crypto_sentiment:
            sentiment_parts.append(
                f"₿ {cls._escape(crypto_sentiment)}"
            )

        if sentiment_parts:
            lines.append(
                " | ".join(sentiment_parts)
            )

        # ======================================================
        # TOP CATALYSTS
        # ======================================================

        lines.append("")

        lines.extend(
            cls._format_catalysts(
                getattr(
                    brief,
                    "catalysts",
                    [],
                )
            )
        )

        # ======================================================
        # INDIAN MARKETS
        # ======================================================

        lines.append("")

        lines.extend(
            cls._format_market_section(
                title="INDIAN MARKETS",
                markets=getattr(
                    brief,
                    "indian_markets",
                    [],
                ),
                flag="🇮🇳",
            )
        )

        # ======================================================
        # TOP INDIAN NEWS
        # ======================================================

        lines.append("")
        lines.extend(
            cls._format_top_news(
                getattr(
                    brief,
                    "top_news",
                    [],
                )
            )
        )

        # ======================================================
        # GLOBAL MARKETS
        # ======================================================

        lines.append("")

        lines.extend(
            cls._format_market_section(
                title="GLOBAL DESK",
                markets=getattr(
                    brief,
                    "global_markets",
                    [],
                ),
                flag="🌍",
            )
        )

        # ======================================================
        # COMMODITIES
        # ======================================================

        lines.extend(
            cls._format_commodities(
                getattr(
                    brief,
                    "commodities",
                    [],
                )
            )
        )

        # ======================================================
        # RADAR
        # ======================================================

        lines.append("")
        lines.append(cls.LINE)
        lines.append(
            "🎯 <b>RADAR &amp; STRATEGY</b>"
        )
        lines.append(cls.LINE)
        lines.append("")

        lines.extend(
            cls._format_stocks_to_watch(
                getattr(
                    brief,
                    "stocks_to_watch",
                    [],
                )
            )
        )

        # ======================================================
        # RISKS
        # ======================================================

        lines.extend(
            cls._format_risks(
                getattr(
                    brief,
                    "risks",
                    [],
                )
            )
        )

        # ======================================================
        # PLAYBOOK
        # ======================================================

        lines.append("")
        lines.append(
            "💡 <b>TODAY'S PLAYBOOK</b>"
        )
        lines.append("")

        playbook = cls._truncate(
            getattr(
                brief,
                "playbook",
                "",
            ),
            cls.MAX_PLAYBOOK_LENGTH,
        )

        if playbook:
            lines.append(
                cls._escape(playbook)
            )
        else:
            lines.append(
                "No playbook available."
            )

        # ======================================================
        # FOOTER
        # ======================================================

        lines.append("")
        lines.append(cls.LINE)
        lines.append(cls.FOOTER)

        return "\n".join(lines)

    # ==========================================================
    # SHORT NEWS-ONLY BROADCAST
    # ==========================================================

    @classmethod
    def top_news(
        cls,
        articles: Iterable[Any] | None,
    ) -> str:
        """
        Format a standalone TOP 5 Indian market news message.

        Useful for:
            - breaking-news jobs
            - afternoon update
            - news-only Telegram messages
        """

        lines = [
            cls.LINE,
            "🇮🇳 <b>INDIAN MARKET NEWS</b>",
            cls.LINE,
            "",
        ]

        lines.extend(
            cls._format_top_news(
                articles
            )
        )

        lines.append("")
        lines.append(cls.LINE)
        lines.append(cls.FOOTER)

        return "\n".join(lines)

    # ==========================================================
    # MARKET SNAPSHOT
    # ==========================================================

    @classmethod
    def market_snapshot(
        cls,
        markets: Iterable[Any] | None,
        title: str = "MARKET SNAPSHOT",
        flag: str = "🇮🇳",
    ) -> str:
        """
        Standalone market snapshot formatter.
        """

        lines = [
            cls.LINE,
            f"{flag} <b>{cls._escape(title)}</b>",
            cls.LINE,
        ]

        lines.extend(
            cls._format_market_section(
                title="",
                markets=markets,
                flag="",
            )
        )

        lines.append("")
        lines.append(cls.LINE)
        lines.append(cls.FOOTER)

        return "\n".join(lines)

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @staticmethod
    def validate(message: str) -> bool:
        """
        Basic formatter validation.

        Returns False for obviously invalid output.
        """

        if not message:
            return False

        if not message.strip():
            return False

        # Telegram messages have a practical size limit.
        if len(message) > 3900:
            return False

        return True

    # ==========================================================
    # SAFE MORNING
    # ==========================================================

    @classmethod
    def safe_morning(
        cls,
        brief: Any,
    ) -> str:
        """
        Format morning brief and guarantee a usable fallback
        instead of allowing formatting errors to propagate.
        """

        try:
            message = cls.morning(
                brief
            )

            if cls.validate(message):
                return message

            raise ValueError(
                "Generated Telegram message failed validation."
            )

        except Exception as exc:
            # Do not expose internal exceptions to Telegram.
            return (
                f"{cls.LINE}\n"
                "🌍 <b>MARKET WAVES</b>\n"
                f"{cls.LINE}\n\n"
                "⚠️ Market brief temporarily unavailable.\n\n"
                "Please try again shortly.\n\n"
                f"{cls.LINE}\n"
                f"{cls.FOOTER}"
            )