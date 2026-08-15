"""
market_sentinel/telegram/morning.py

Production-grade Telegram Morning Brief Formatter.

Responsibilities:
    - Format executive market summary
    - Format Indian market indices
    - Format sector performance
    - Format top gainers / losers
    - Format TOP 5 Indian market news
    - Safely escape Telegram HTML
    - Keep messages within Telegram limits
    - Prevent duplicate news presentation
    - Handle incomplete / optional data safely

Author  : Market Wavez
Version : 3.0.0
"""

from __future__ import annotations

from html import escape
from typing import Any

from market_sentinel.briefs.models import MorningBrief


class MorningFormatter:
    """
    Production Telegram formatter for Morning Brief.

    Telegram uses HTML parse mode.

    The formatter deliberately keeps TOP 5 news in the
    executive message and does NOT repeat the same articles
    in a second "TOP MARKET NEWS" section.
    """

    LINE = "━━━━━━━━━━━━━━━━━━━━"
    SHORT_LINE = "────────────────────"

    MAX_TOP_NEWS = 5
    MAX_GAINERS = 5
    MAX_LOSERS = 5

    # Telegram has a 4096-character message limit.
    # Keep a safety margin.
    TELEGRAM_MAX_LENGTH = 4000

    # ==========================================================
    # MAIN FORMATTER
    # ==========================================================

    @classmethod
    def format(
        cls,
        brief: MorningBrief,
    ) -> list[str]:
        """
        Convert MorningBrief into Telegram messages.

        Message structure:

            1. Executive Summary + TOP 5 Indian News
            2. Indian Markets
            3. Sector Heatmap
            4. Top Gainers / Losers

        Returns:
            list[str]: Telegram-ready HTML messages.
        """

        messages: list[str] = []

        # ------------------------------------------------------
        # MESSAGE 1
        # Executive Summary + TOP 5
        # ------------------------------------------------------

        messages.append(
            cls._build_executive_message(brief)
        )

        # ------------------------------------------------------
        # MESSAGE 2
        # Indian Markets
        # ------------------------------------------------------

        if brief.indices:
            messages.append(
                cls._build_indices_message(brief)
            )

        # ------------------------------------------------------
        # MESSAGE 3
        # Sector Heatmap
        # ------------------------------------------------------

        if brief.sectors:
            messages.append(
                cls._build_sector_message(brief)
            )

        # ------------------------------------------------------
        # MESSAGE 4
        # Top Movers
        # ------------------------------------------------------

        if brief.gainers or brief.losers:
            messages.append(
                cls._build_movers_message(brief)
            )

        return [
            cls._fit_telegram_limit(message)
            for message in messages
            if message.strip()
        ]

    # ==========================================================
    # MESSAGE 1
    # ==========================================================

    @classmethod
    def _build_executive_message(
        cls,
        brief: MorningBrief,
    ) -> str:
        """Build executive summary and TOP 5 Indian market news."""

        lines: list[str] = []

        sentiment = (
            getattr(
                brief,
                "market_sentiment",
                None,
            )
            or "Neutral"
        )

        sentiment_emoji = cls._sentiment_emoji(
            sentiment
        )

        generated_at = getattr(
            brief,
            "generated_at",
            None,
        )

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        lines.append(cls.LINE)
        lines.append(
            "🇮🇳 <b>MARKET WAVES — INDIA MORNING BRIEF</b>"
        )
        lines.append(cls.LINE)

        if generated_at:

            lines.append(
                f"📅 <b>{generated_at:%d %b %Y}</b>"
                f" | ⏰ <b>{generated_at:%I:%M %p} IST</b>"
            )

        lines.append("")

        # ------------------------------------------------------
        # Market Health
        # ------------------------------------------------------

        health_score = cls._safe_number(
            getattr(
                brief,
                "health_score",
                0,
            )
        )

        confidence = cls._safe_number(
            getattr(
                brief,
                "confidence",
                0,
            )
        )

        lines.append(
            f"🩺 <b>Market Health:</b> "
            f"{cls._health_emoji(health_score)} "
            f"<code>{health_score:.0f}/100</code> "
            f"<b>{cls._health_label(health_score)}</b>"
        )

        lines.append(
            f"🐂 <b>Sentiment:</b> "
            f"<b>{escape(str(sentiment))}</b> "
            f"({confidence:.0f}% confidence) "
            f"{sentiment_emoji}"
        )

        lines.append("")

        # ------------------------------------------------------
        # TOP 5
        # ------------------------------------------------------

        lines.append(
            "📰 <b>TOP 5 THINGS TODAY</b>"
        )

        lines.append(cls.LINE)

        top_news = list(
            getattr(
                brief,
                "top_news",
                None,
            )
            or []
        )

        if not top_news:

            lines.append(
                "ℹ️ No major Indian market-moving "
                "news detected."
            )

        else:

            selected_news = cls._select_unique_news(
                top_news,
                limit=cls.MAX_TOP_NEWS,
            )

            for number, article in enumerate(
                selected_news,
                start=1,
            ):

                lines.extend(
                    cls._news_block(
                        article,
                        number,
                    )
                )

                if number < len(selected_news):
                    lines.append("")

        lines.append("")
        lines.append(cls.LINE)

        lines.append(
            "⚡ <i>India-first market intelligence | "
            "News ranked by relevance, impact and recency</i>"
        )

        return "\n".join(lines)

    # ==========================================================
    # NEWS BLOCK
    # ==========================================================

    @classmethod
    def _news_block(
        cls,
        article: Any,
        number: int,
    ) -> list[str]:
        """
        Format one news article.

        Supports the current NewsArticle model while
        gracefully handling future intelligence fields.
        """

        lines: list[str] = []

        title = (
            getattr(
                article,
                "title",
                None,
            )
            or "Market update"
        )

        source = (
            getattr(
                article,
                "source",
                None,
            )
            or "Unknown source"
        )

        url = (
            getattr(
                article,
                "url",
                None,
            )
            or ""
        ).strip()

        summary = (
            getattr(
                article,
                "summary",
                None,
            )
            or ""
        ).strip()

        score = cls._safe_number(
            getattr(
                article,
                "score",
                0,
            )
        )

        impact = cls._safe_number(
            getattr(
                article,
                "impact",
                0,
            )
        )

        importance = cls._safe_number(
            getattr(
                article,
                "importance",
                0,
            )
        )

        category = (
            getattr(
                article,
                "category",
                None,
            )
            or "Market News"
        )

        entities = (
            getattr(
                article,
                "entities",
                None,
            )
            or []
        )

        sectors = (
            getattr(
                article,
                "sectors",
                None,
            )
            or []
        )

        published_at = getattr(
            article,
            "published_at",
            None,
        )

        # ------------------------------------------------------
        # Number + severity
        # ------------------------------------------------------

        severity = cls._news_severity(
            score,
            impact,
            importance,
        )

        lines.append(
            f"{severity} <b>{number}. "
            f"{escape(str(title))}</b>"
        )

        # ------------------------------------------------------
        # Score
        # ------------------------------------------------------

        if score > 0:

            lines.append(
                f"   🎯 <b>Impact Score:</b> "
                f"<code>{score:.0f}/100</code> "
                f"{cls._score_label(score)}"
            )

        # ------------------------------------------------------
        # Category
        # ------------------------------------------------------

        category_text = cls._enum_text(
            category
        )

        if category_text:

            lines.append(
                f"   🏷 <b>Event:</b> "
                f"{escape(category_text)}"
            )

        # ------------------------------------------------------
        # Entities
        # ------------------------------------------------------

        entity_text = cls._format_list(
            entities,
            limit=5,
        )

        if entity_text:

            lines.append(
                f"   🏢 <b>Entities:</b> "
                f"{escape(entity_text)}"
            )

        # ------------------------------------------------------
        # Sectors
        # ------------------------------------------------------

        sector_text = cls._format_list(
            sectors,
            limit=4,
        )

        if sector_text:

            lines.append(
                f"   📌 <b>Sectors:</b> "
                f"{escape(sector_text)}"
            )

        # ------------------------------------------------------
        # Summary
        # ------------------------------------------------------

        clean_summary = cls._clean_summary(
            summary
        )

        if clean_summary:

            clean_summary = cls._truncate(
                clean_summary,
                220,
            )

            lines.append(
                f"   💡 {escape(clean_summary)}"
            )

        # ------------------------------------------------------
        # Source
        # ------------------------------------------------------

        lines.append(
            f"   📰 <b>Source:</b> "
            f"{escape(str(source))}"
        )

        # ------------------------------------------------------
        # Published time
        # ------------------------------------------------------

        if published_at:

            lines.append(
                "   🕒 <b>Published:</b> "
                f"{cls._format_datetime(published_at)}"
            )

        # ------------------------------------------------------
        # Read article
        # ------------------------------------------------------

        if url:

            safe_url = escape(
                url,
                quote=True,
            )

            lines.append(
                f'   🔎 <a href="{safe_url}">'
                f"Read Full Story</a>"
            )

        return lines

    # ==========================================================
    # MESSAGE 2 — INDIAN MARKETS
    # ==========================================================

    @classmethod
    def _build_indices_message(
        cls,
        brief: MorningBrief,
    ) -> str:
        """Build Indian indices section."""

        lines: list[str] = []

        lines.append(
            "📊 <b>INDIAN MARKETS</b>"
        )

        lines.append(cls.LINE)

        indices = list(
            getattr(
                brief,
                "indices",
                None,
            )
            or []
        )

        up = sorted(
            [
                index
                for index in indices
                if cls._safe_number(
                    getattr(
                        index,
                        "percent_change",
                        0,
                    )
                ) >= 0
            ],
            key=lambda item: cls._safe_number(
                getattr(
                    item,
                    "percent_change",
                    0,
                )
            ),
            reverse=True,
        )

        down = sorted(
            [
                index
                for index in indices
                if cls._safe_number(
                    getattr(
                        index,
                        "percent_change",
                        0,
                    )
                ) < 0
            ],
            key=lambda item: cls._safe_number(
                getattr(
                    item,
                    "percent_change",
                    0,
                )
            ),
        )

        if up:

            lines.append("")
            lines.append("🟢 <b>GAINING</b>")
            lines.append("")

            for index in up:
                lines.append(
                    cls._market_row(index)
                )

        if down:

            lines.append("")
            lines.append("🔴 <b>DECLINING</b>")
            lines.append("")

            for index in down:
                lines.append(
                    cls._market_row(index)
                )

        return "\n".join(lines)

    # ==========================================================
    # MESSAGE 3 — SECTORS
    # ==========================================================

    @classmethod
    def _build_sector_message(
        cls,
        brief: MorningBrief,
    ) -> str:
        """Build sector heatmap."""

        lines: list[str] = []

        lines.append(
            "🌡 <b>SECTOR HEATMAP</b>"
        )

        lines.append(cls.LINE)

        sectors = sorted(
            list(
                getattr(
                    brief,
                    "sectors",
                    None,
                )
                or []
            ),
            key=lambda item: cls._safe_number(
                getattr(
                    item,
                    "percent_change",
                    0,
                )
            ),
            reverse=True,
        )

        positive: list[str] = []
        neutral: list[str] = []
        negative: list[str] = []

        for sector in sectors:

            change = cls._safe_number(
                getattr(
                    sector,
                    "percent_change",
                    0,
                )
            )

            row = cls._sector_row(
                sector
            )

            if change > 0.20:
                positive.append(row)

            elif change < -0.20:
                negative.append(row)

            else:
                neutral.append(row)

        if positive:

            lines.append("")
            lines.append("🟢 <b>BULLISH</b>")
            lines.append("")
            lines.extend(positive)

        if neutral:

            lines.append("")
            lines.append("🟡 <b>NEUTRAL</b>")
            lines.append("")
            lines.extend(neutral)

        if negative:

            lines.append("")
            lines.append("🔴 <b>BEARISH</b>")
            lines.append("")
            lines.extend(negative)

        return "\n".join(lines)

    # ==========================================================
    # MESSAGE 4 — MOVERS
    # ==========================================================

    @classmethod
    def _build_movers_message(
        cls,
        brief: MorningBrief,
    ) -> str:
        """Build top gainers and losers."""

        lines: list[str] = []

        gainers = sorted(
            list(
                getattr(
                    brief,
                    "gainers",
                    None,
                )
                or []
            ),
            key=lambda item: cls._safe_number(
                getattr(
                    item,
                    "percent_change",
                    0,
                )
            ),
            reverse=True,
        )

        losers = sorted(
            list(
                getattr(
                    brief,
                    "losers",
                    None,
                )
                or []
            ),
            key=lambda item: cls._safe_number(
                getattr(
                    item,
                    "percent_change",
                    0,
                )
            ),
        )

        if gainers:

            lines.append(
                "🚀 <b>TOP GAINERS</b>"
            )

            lines.append(cls.LINE)
            lines.append("")

            for stock in gainers[
                :cls.MAX_GAINERS
            ]:

                lines.append(
                    cls._stock_row(
                        stock,
                        direction="up",
                    )
                )

        if losers:

            if gainers:
                lines.append("")

            lines.append(
                "🩸 <b>TOP LOSERS</b>"
            )

            lines.append(cls.LINE)
            lines.append("")

            for stock in losers[
                :cls.MAX_LOSERS
            ]:

                lines.append(
                    cls._stock_row(
                        stock,
                        direction="down",
                    )
                )

        return "\n".join(lines)

    # ==========================================================
    # MARKET ROW
    # ==========================================================

    @staticmethod
    def _market_row(
        index: Any,
    ) -> str:
        """Format one market index."""

        change = MorningFormatter._safe_number(
            getattr(
                index,
                "percent_change",
                0,
            )
        )

        value = MorningFormatter._safe_number(
            getattr(
                index,
                "value",
                0,
            )
        )

        raw_name = (
            getattr(
                index,
                "name",
                None,
            )
            or "INDEX"
        )

        name = MorningFormatter._short_index_name(
            str(raw_name)
        )

        if change >= 0:

            icon = "📈"
            arrow = "▲"

        else:

            icon = "📉"
            arrow = "▼"

        return (
            f"{icon} <b>{escape(name)}</b> : "
            f"<code>{value:,.2f}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    # ==========================================================
    # SECTOR ROW
    # ==========================================================

    @staticmethod
    def _sector_row(
        sector: Any,
    ) -> str:
        """Format one sector."""

        change = MorningFormatter._safe_number(
            getattr(
                sector,
                "percent_change",
                0,
            )
        )

        raw_name = (
            getattr(
                sector,
                "name",
                None,
            )
            or "Sector"
        )

        name = MorningFormatter._short_sector_name(
            str(raw_name)
        )

        arrow = "▲" if change >= 0 else "▼"

        dots = "." * max(
            5,
            18 - len(name),
        )

        return (
            f"• <b>{escape(name)}</b> "
            f"<code>{dots}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    # ==========================================================
    # STOCK ROW
    # ==========================================================

    @staticmethod
    def _stock_row(
        stock: Any,
        direction: str,
    ) -> str:
        """Format one stock mover."""

        change = MorningFormatter._safe_number(
            getattr(
                stock,
                "percent_change",
                0,
            )
        )

        value = MorningFormatter._safe_number(
            getattr(
                stock,
                "value",
                0,
            )
        )

        raw_name = (
            getattr(
                stock,
                "name",
                None,
            )
            or "STOCK"
        )

        name = MorningFormatter._short_stock_name(
            str(raw_name)
        )

        if direction == "up":

            icon = "📈"
            arrow = "▲"

        else:

            icon = "📉"
            arrow = "▼"

        return (
            f"{icon} <b>{escape(name)}</b>"
            f" | <code>₹{value:,.2f}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    # ==========================================================
    # NEWS SELECTION
    # ==========================================================

    @classmethod
    def _select_unique_news(
        cls,
        articles: list[Any],
        limit: int,
    ) -> list[Any]:
        """
        Remove duplicate news articles.

        Deduplication is based on:
            1. URL
            2. normalized title
        """

        selected: list[Any] = []

        seen_urls: set[str] = set()
        seen_titles: set[str] = set()

        for article in articles:

            url = (
                getattr(
                    article,
                    "url",
                    None,
                )
                or ""
            ).strip().lower()

            title = (
                getattr(
                    article,
                    "title",
                    None,
                )
                or ""
            ).strip().lower()

            normalized_title = " ".join(
                title.split()
            )

            if url and url in seen_urls:
                continue

            if (
                normalized_title
                and normalized_title in seen_titles
            ):
                continue

            if url:
                seen_urls.add(url)

            if normalized_title:
                seen_titles.add(
                    normalized_title
                )

            selected.append(article)

            if len(selected) >= limit:
                break

        return selected

    # ==========================================================
    # TEXT HELPERS
    # ==========================================================

    @staticmethod
    def _clean_summary(
        summary: str,
    ) -> str:
        """Clean RSS summary text."""

        summary = summary.strip()

        # Remove simple HTML tags from RSS descriptions.
        import re

        summary = re.sub(
            r"<[^>]+>",
            " ",
            summary,
        )

        summary = re.sub(
            r"\s+",
            " ",
            summary,
        )

        return summary.strip()

    @staticmethod
    def _truncate(
        text: str,
        maximum: int,
    ) -> str:
        """Safely truncate text."""

        if len(text) <= maximum:
            return text

        return (
            text[: maximum - 1].rstrip()
            + "…"
        )

    @staticmethod
    def _format_list(
        values: Any,
        limit: int,
    ) -> str:
        """Format list-like metadata."""

        if not values:
            return ""

        if isinstance(
            values,
            str,
        ):
            return values

        result: list[str] = []

        for value in values[:limit]:

            text = MorningFormatter._enum_text(
                value
            )

            if text:
                result.append(text)

        return ", ".join(result)

    @staticmethod
    def _enum_text(
        value: Any,
    ) -> str:
        """Convert enums / values to display text."""

        if value is None:
            return ""

        raw = getattr(
            value,
            "value",
            value,
        )

        return str(raw).replace(
            "_",
            " ",
        ).strip()

    @staticmethod
    def _safe_number(
        value: Any,
    ) -> float:
        """Safely convert a value to float."""

        try:
            return float(value or 0)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _fit_telegram_limit(
        message: str,
    ) -> str:
        """Prevent Telegram message overflow."""

        if len(message) <= MorningFormatter.TELEGRAM_MAX_LENGTH:
            return message

        return (
            message[
                :MorningFormatter.TELEGRAM_MAX_LENGTH
                - 30
            ].rstrip()
            + "\n\n<i>Message truncated.</i>"
        )

    # ==========================================================
    # SENTIMENT
    # ==========================================================

    @staticmethod
    def _sentiment_emoji(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).strip().lower()

        if value in {
            "bullish",
            "strong bullish",
            "very bullish",
        }:
            return "🟢"

        if value in {
            "bearish",
            "strong bearish",
            "very bearish",
        }:
            return "🔴"

        return "🟡"

    # ==========================================================
    # HEALTH
    # ==========================================================

    @staticmethod
    def _health_emoji(
        score: float,
    ) -> str:

        if score >= 65:
            return "🟢"

        if score >= 45:
            return "🟡"

        if score >= 30:
            return "🟠"

        return "🔴"

    @staticmethod
    def _health_label(
        score: float,
    ) -> str:

        if score >= 80:
            return "EXCELLENT"

        if score >= 65:
            return "HEALTHY"

        if score >= 50:
            return "NEUTRAL"

        if score >= 35:
            return "WEAK"

        return "POOR"

    # ==========================================================
    # NEWS SCORE
    # ==========================================================

    @staticmethod
    def _score_label(
        score: float,
    ) -> str:

        if score >= 90:
            return "🚨 EXCEPTIONAL"

        if score >= 80:
            return "🔥 VERY HIGH"

        if score >= 70:
            return "⚡ HIGH"

        if score >= 55:
            return "🟡 MEDIUM"

        return "⚪ LOW"

    @staticmethod
    def _news_severity(
        score: float,
        impact: float,
        importance: float,
    ) -> str:
        """
        Select visual severity based on the strongest
        available intelligence score.
        """

        effective_score = max(
            score,
            impact,
            importance,
        )

        if effective_score >= 85:
            return "🚨"

        if effective_score >= 70:
            return "⚡"

        if effective_score >= 50:
            return "📌"

        return "📰"

    # ==========================================================
    # DATETIME
    # ==========================================================

    @staticmethod
    def _format_datetime(
        value: Any,
    ) -> str:
        """Format publication timestamp."""

        try:

            return value.strftime(
                "%d %b %Y | %I:%M %p IST"
            )

        except (
            AttributeError,
            ValueError,
        ):

            return str(value)

    # ==========================================================
    # SHORT INDEX NAMES
    # ==========================================================

    @staticmethod
    def _short_index_name(
        name: str,
    ) -> str:

        mapping = {
            "NIFTY 50": "NIFTY",
            "NIFTY": "NIFTY",
            "NIFTY BANK": "BANKNIFTY",
            "BANKNIFTY": "BANKNIFTY",
            "NIFTY FIN SERVICE": "FINNIFTY",
            "FINNIFTY": "FINNIFTY",
            "NIFTY MIDCAP SELECT": "MIDCAP",
            "NIFTY MIDCAP 50": "MIDCAP",
            "NIFTY IT": "NIFTY IT",
            "NIFTY PHARMA": "NIFTY PHARMA",
            "INDIA VIX": "INDIA VIX",
        }

        cleaned = (
            name
            or ""
        ).strip()

        return mapping.get(
            cleaned,
            cleaned,
        )

    # ==========================================================
    # SHORT SECTOR NAMES
    # ==========================================================

    @staticmethod
    def _short_sector_name(
        name: str,
    ) -> str:

        mapping = {
            "Nifty Pharma": "Pharma",
            "NIFTY PHARMA": "Pharma",
            "Nifty PSU Bank": "PSU Bank",
            "NIFTY PSU BANK": "PSU Bank",
            "Nifty Metal": "Metal",
            "NIFTY METAL": "Metal",
            "Nifty Media": "Media",
            "NIFTY MEDIA": "Media",
            "Nifty Energy": "Energy",
            "NIFTY ENERGY": "Energy",
            "Nifty FMCG": "FMCG",
            "NIFTY FMCG": "FMCG",
            "Nifty Auto": "Auto",
            "NIFTY AUTO": "Auto",
            "Nifty Realty": "Realty",
            "NIFTY REALTY": "Realty",
            "Nifty IT": "IT",
            "NIFTY IT": "IT",
        }

        cleaned = (
            name
            or ""
        ).strip()

        return mapping.get(
            cleaned,
            cleaned.replace(
                "Nifty ",
                "",
            ).replace(
                "NIFTY ",
                "",
            ),
        )

    # ==========================================================
    # SHORT STOCK NAMES
    # ==========================================================

    @staticmethod
    def _short_stock_name(
        name: str,
    ) -> str:

        cleaned = (
            name
            or ""
        ).strip()

        mapping = {
            "GODREJ CONSUMER": "GODREJCP",
            "GODREJ CONSUMER PRODUCTS": "GODREJCP",
            "PIRAMAL ENTERPRISES": "PIRAMAL",
            "FORTIS HEALTHCARE": "FORTIS",
            "TATA CONSULTANCY SERVICES": "TCS",
            "MAX HEALTHCARE": "MAXHEALTH",
            "BSE LIMITED": "BSE",
            "UNO MINDA": "UNOMINDA",
            "LARSEN & TOUBRO": "LT",
            "KPIT TECHNOLOGIES": "KPITTECH",
            "POWER INDIA": "POWERINDIA",
            "NATIONAL ALUMINIUM": "NATIONALUM",
            "BHARAT HEAVY ELECTRICALS": "BHEL",
            "INDUS TOWERS": "INDUSTOWER",
            "KAYNES TECHNOLOGY": "KAYNES",
        }

        if cleaned in mapping:
            return mapping[cleaned]

        return cleaned[:12]