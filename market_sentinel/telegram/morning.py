"""
telegram/morning.py

Formats the Morning Brief for Telegram.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.briefs.models import MorningBrief


class MorningFormatter:

    LINE = "──────────────"

    @staticmethod
    def format(
        brief: MorningBrief,
    ) -> list[str]:

        messages = []

        # =====================================================
        # Message 1
        # =====================================================

        lines = []

        icon = "🟢"

        if brief.market_sentiment == "Bearish":
            icon = "🔴"
        elif brief.market_sentiment == "Neutral":
            icon = "🟡"

        lines.append("📈 <b>MARKET WAVEZ | MORNING BRIEF</b>")
        lines.append(
            f"📅 {brief.generated_at:%d %b %Y} | 🕣 {brief.generated_at:%I:%M %p}"
        )

        lines.extend(
            MorningFormatter._header(
                "📊 Market Health"
            )
        )

        lines.append(f"Score      : {brief.health_score}/100")
        lines.append(f"Sentiment  : {icon} {brief.market_sentiment}")
        lines.append(f"Confidence : {brief.confidence}%")

        lines.extend(
            MorningFormatter._header(
                "🇮🇳 Indian Indices"
            )
        )

        rows = [
            MorningFormatter._index_row(index)
            for index in brief.indices
        ]

        lines.extend(
            MorningFormatter._table(rows)
        )

        messages.append(
            "\n".join(lines)
        )

        # =====================================================
        # Message 2
        # =====================================================

        if brief.sectors:

            lines = []

            lines.extend(
                MorningFormatter._header(
                    "🟩 Sector Heatmap"
                )
            )

            rows = [
                MorningFormatter._index_row(sector)
                for sector in brief.sectors
            ]

            lines.extend(
                MorningFormatter._table(rows)
            )

            messages.append(
                "\n".join(lines)
            )

        # =====================================================
        # Message 3 : Top Gainers
        # =====================================================

        if brief.gainers:

            lines = []

            lines.extend(
                MorningFormatter._header(
                    "🏆 Top Gainers"
                )
            )

            rows = []

            for stock in brief.gainers:
                rows.append(
                    MorningFormatter._stock_row(stock)
                )

            lines.extend(
                MorningFormatter._table(rows)
            )

            messages.append(
                "\n".join(lines)
            )

        # =====================================================
        # Message 4 : Top Losers
        # =====================================================

        if brief.losers:

            lines = []

            lines.extend(
                MorningFormatter._header(
                    "🩸 Top Losers"
                )
            )

            rows = []

            for stock in sorted(
                    brief.losers,
                    key=lambda s: s.percent_change
            ):
                rows.append(
                    MorningFormatter._stock_row(stock)
                )

            lines.extend(
                MorningFormatter._table(rows)
            )

            messages.append(
                "\n".join(lines)
            )

        # =====================================================
        # Message 5 : Top Market News
        # =====================================================

        if brief.top_news:

            lines = []

            lines.extend(
                MorningFormatter._header("📰 Top Market News")
            )

            for article in brief.top_news[:8]:

                lines.append(f"🔥 <b>{article.title}</b>")

                if article.entities:
                    lines.append(
                        f"🏢 {', '.join(article.entities[:3])}"
                    )

                if article.url:
                    lines.append(
                        f'🔗 <a href="{article.url}">Read More →</a>'
                    )

                lines.append("")

            messages.append(
                "\n".join(lines)
            )

        return messages
    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _header(title: str) -> list[str]:

        return [
            "",
            MorningFormatter.LINE,
            f"<b>{title}</b>",
            MorningFormatter.LINE,
            "",
        ]

    @staticmethod
    def _index_row(index) -> str:

        arrow = "▲" if index.percent_change >= 0 else "▼"

        return (
            f"{index.name[:16]:<16}"
            f"{index.value:>12,.2f}"
            f"{arrow}{abs(index.percent_change):>7.2f}%"
        )

    @staticmethod
    def _stock_row(stock) -> str:

        arrow = "▲" if stock.percent_change >= 0 else "▼"

        return (
            f"{stock.name[:16]:<16}"
            f"{stock.value:>12,.2f}"
            f"{arrow}{abs(stock.percent_change):>7.2f}%"
        )

    @staticmethod
    def _table(rows: list[str]) -> list[str]:

        return [
            "<pre>",
            f"{'NAME':<16}{'PRICE':>12}{'%':>8}",
            "────────────────────────────",
            *rows,
            "</pre>",
        ]