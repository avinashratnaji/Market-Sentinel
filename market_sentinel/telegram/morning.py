"""
telegram/morning.py

Formats the Morning Brief for Telegram.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.briefs.models import MorningBrief


class MorningFormatter:

    @staticmethod
    def format(
        brief: MorningBrief,
    ) -> str:

        lines = []

        lines.append("📈 MARKET SENTINEL | MORNING BRIEF")

        lines.append(
            f"📅 {brief.generated_at:%d %b %Y} | 🕣 {brief.generated_at:%I:%M %p}"
        )

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        icon = "🟢"

        if brief.market_sentiment == "Bearish":
            icon = "🔴"

        elif brief.market_sentiment == "Neutral":
            icon = "🟡"

        lines.append(
            f"📊 Market Health: {brief.health_score}/100 | {icon} {brief.market_sentiment} | Confidence: {brief.confidence}%"
        )

        # ----------------------------------------------------
        # Indices
        # ----------------------------------------------------

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🇮🇳 INDIAN INDICES")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for index in brief.indices:
            lines.append(
                index.telegram_line,
            )

        # ----------------------------------------------------
        # Sector Heatmap
        # ----------------------------------------------------

        if brief.sectors:

            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("🟩 INDIA SECTOR HEATMAP")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")

            for sector in brief.sectors:

                lines.append(
                    sector.telegram_line,
                )

        # ----------------------------------------------------
        # Gainers
        # ----------------------------------------------------

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🏆 TOP GAINERS")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for stock in brief.gainers:

            lines.append(
                stock.telegram_line,
            )

        # ----------------------------------------------------
        # Losers
        # ----------------------------------------------------

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🩸 TOP LOSERS")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for stock in brief.losers:

            lines.append(
                stock.telegram_line,
            )

        # ----------------------------------------------------
        # Top Market News
        # ----------------------------------------------------

        if brief.top_news:

            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("📰 TOP MARKET NEWS")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")

            for article in brief.top_news:

                lines.append(
                    f"🔥 {article.title}"
                )

                if article.entities:

                    lines.append(
                        f"   🏢 {', '.join(article.entities)}"
                    )

                lines.append(
                    f"   📂 {article.category.value} | ⭐ {article.score}"
                )

                lines.append("")

        return "\n".join(lines)