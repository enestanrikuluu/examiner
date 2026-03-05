"""PDF export for exam analytics reports.

Uses a simple HTML-to-text approach stored as a text report.
Full PDF rendering (via weasyprint/reportlab) can be added when the
dependency is installed; this module provides the data preparation and
a plain-text fallback.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import TopicMastery
from src.analytics.service import AnalyticsService


async def generate_report_text(
    db: AsyncSession,
    template_id: uuid.UUID,
) -> str:
    """Generate a plain-text analytics report for a template.

    This can be used as-is or converted to PDF via weasyprint/reportlab.
    """
    svc = AnalyticsService(db)

    # Gather data
    score_dist = await svc.score_distribution(template_id)
    item_data = await svc.item_analysis(template_id)
    mastery = await svc.topic_mastery(template_id)
    ai_costs = await svc.ai_costs(template_id=template_id)

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("SINAV ANALIZ RAPORU")
    lines.append(f"Tarih: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Sablon ID: {template_id}")
    lines.append("=" * 60)
    lines.append("")

    # Score Distribution
    lines.append("1. PUAN DAGILIMI")
    lines.append("-" * 40)
    lines.append(f"  Toplam oturum:    {score_dist.total_sessions}")
    lines.append(f"  Notlanan oturum:  {score_dist.graded_sessions}")
    if score_dist.mean_score is not None:
        lines.append(f"  Ortalama:         %{score_dist.mean_score}")
        lines.append(f"  Medyan:           %{score_dist.median_score}")
        lines.append(f"  Std sapma:        {score_dist.std_dev}")
        lines.append(f"  Min/Max:          %{score_dist.min_score} / %{score_dist.max_score}")
        lines.append(f"  Gecme orani:      %{score_dist.pass_rate}")
    lines.append("")

    if score_dist.distribution:
        lines.append("  Aralik        Sayi")
        for b in score_dist.distribution:
            bar = "#" * b.count
            lines.append(f"  {b.range_start:5.1f}-{b.range_end:5.1f}  {b.count:4d}  {bar}")
    lines.append("")

    # Item Analysis
    lines.append("2. SORU ANALIZI")
    lines.append("-" * 40)
    lines.append(f"  Toplam soru: {item_data.total_items}")
    lines.append("")
    if item_data.items:
        lines.append(f"  {'Soru ID':<12} {'Tip':<12} {'P-degeri':>10} {'Cevap':>8} {'Konu':<20}")
        for item in item_data.items[:20]:
            lines.append(
                f"  {str(item.question_id)[:8]:<12} "
                f"{item.question_type:<12} "
                f"{item.p_value:>10.4f} "
                f"{item.response_count:>8} "
                f"{(item.topic or '-'):<20}"
            )
    lines.append("")

    # Topic Mastery
    lines.append("3. KONU HAKIMIYETI")
    lines.append("-" * 40)
    if isinstance(mastery.mastery, list) and mastery.mastery:
        lines.append(f"  {'Konu':<30} {'Cevap':>8} {'Dogru':>8} {'Oran':>8}")
        for tm in mastery.mastery:
            if not isinstance(tm, TopicMastery):
                continue
            lines.append(
                f"  {tm.topic:<30} "
                f"{tm.response_count:>8} "
                f"{tm.correct_count:>8} "
                f"{tm.mastery_rate:>8.2%}"
            )
    lines.append("")

    # AI Costs
    lines.append("4. AI MALIYETLERI")
    lines.append("-" * 40)
    lines.append(f"  Toplam maliyet: ${ai_costs.total_cost_usd:.4f}")
    lines.append(f"  Toplam cagri:   {ai_costs.total_calls}")
    if ai_costs.by_task:
        lines.append("")
        lines.append(f"  {'Gorev':<15} {'Cagri':>8} {'Maliyet':>12}")
        for t in ai_costs.by_task:
            lines.append(
                f"  {t.task_type:<15} {t.call_count:>8} ${t.total_cost_usd:>11.4f}"
            )
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
