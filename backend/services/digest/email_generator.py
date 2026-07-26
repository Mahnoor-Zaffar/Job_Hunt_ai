from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from backend.services.digest.config import DigestConfig
from backend.services.digest.models import CategoryGroup, ScoredJob


def generate_email_html(
    categories: list[CategoryGroup],
    config: DigestConfig,
    stats: dict[str, Any] | None = None,
) -> str:
    date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    sections_html = ""
    total_jobs = 0
    for group in categories:
        cat_jobs_html = ""
        for sj in group.jobs:
            cat_jobs_html += _job_to_html(sj)
            total_jobs += 1

        sections_html += f"""
        <div style="margin-bottom: 32px;">
            <h2 style="font-size: 18px; font-weight: 600; color: #111; margin: 0 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #6366f1;">
                {group.category_label}
            </h2>
            {cat_jobs_html}
        </div>
        """

    stats_html = ""
    if stats:
        stats_html = f"""
        <div style="margin: 24px 0; padding: 12px 16px; background: #f8fafc; border-radius: 8px; font-size: 12px; color: #64748b;">
            Processed {stats.get('total_scraped', 0)} jobs &middot;
            Accepted {stats.get('accepted', 0)} &middot;
            Rejected {stats.get('rejected', 0)} &middot;
            Duplicates removed {stats.get('duplicates_removed', 0)}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background: #f0f0f0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: #f0f0f0;">
        <tr><td style="padding: 24px 16px;">
            <table width="600" cellpadding="0" cellspacing="0" style="margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <tr>
                    <td style="padding: 24px 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6);">
                        <h1 style="font-size: 22px; font-weight: 700; color: #fff; margin: 0 0 4px 0;">Daily Job Digest</h1>
                        <p style="font-size: 14px; color: rgba(255,255,255,0.85); margin: 0;">{date_str}</p>
                    </td>
                </tr>
                {stats_html}
                <tr><td style="padding: 24px 32px;">
                    {sections_html if sections_html else '<p style="color: #64748b; text-align: center; padding: 32px 0;">No matching jobs found for today.</p>'}
                </td></tr>
                <tr>
                    <td style="padding: 16px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0;">
                        <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                            Job Hunting AI · Curated based on your preferences
                        </p>
                    </td>
                </tr>
            </table>
        </td></tr>
    </table>
</body>
</html>"""

    return html


def generate_email_text(categories: list[CategoryGroup], config: DigestConfig, stats: dict[str, Any] | None = None) -> str:
    date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    lines = [f"Daily Job Digest - {date_str}", "=" * 40, ""]

    if stats:
        lines.append(f"Processed: {stats.get('total_scraped', 0)} | Accepted: {stats.get('accepted', 0)} | Rejected: {stats.get('rejected', 0)}")
        lines.append("")

    for group in categories:
        lines.append(f"# {group.category_label}")
        lines.append("")
        for sj in group.jobs:
            lines.append(f"  {sj.job.title}")
            lines.append(f"  {sj.job.company}")
            lines.append(f"  {_format_location(sj.job)}")
            salary = _format_salary(sj.job.salary_min, sj.job.salary_max, sj.job.currency)
            if salary:
                lines.append(f"  {salary}")
            if sj.job.apply_url:
                lines.append(f"  Apply: {sj.job.apply_url}")
            lines.append(f"  Confidence: {sj.confidence}")
            lines.append("")
        lines.append("")

    lines.append("---")
    lines.append("Job Hunting AI · Curated based on your preferences")
    return "\n".join(lines)


def _job_to_html(sj: ScoredJob) -> str:
    job = sj.job
    location = _format_location(job)
    salary = _format_salary(job.salary_min, job.salary_max, job.currency)
    posted = _format_posted(job.posted_at)
    skills_html = ""
    if job.skills:
        skill_tags = "".join(
            f'<span style="display: inline-block; font-size: 11px; color: #6366f1; background: #eef2ff; padding: 2px 8px; border-radius: 4px; margin: 2px 4px 2px 0;">{s}</span>'
            for s in job.skills[:8]
        )
        if skill_tags:
            skills_html = f'<div style="margin-top: 8px;">{skill_tags}</div>'

    conf_badge_color = "#22c55e" if sj.confidence == "high" else "#eab308"
    conf_badge_label = "HIGH" if sj.confidence == "high" else "MED"

    apply_link = ""
    if job.apply_url:
        apply_link = f'<a href="{job.apply_url}" style="display: inline-block; padding: 6px 16px; background: #6366f1; color: #fff; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 500;">Apply</a>'

    return f"""
    <div style="padding: 14px 16px; margin-bottom: 10px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #6366f1;">
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td>
                    <div style="font-size: 14px; font-weight: 600; color: #111;">{job.title}</div>
                    <div style="font-size: 13px; color: #475569; margin-top: 2px;">{job.company}</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                        {location}
                        {f' &middot; {salary}' if salary else ''}
                        {f' &middot; {posted}' if posted else ''}
                    </div>
                    {skills_html}
                </td>
                <td style="text-align: right; vertical-align: middle; white-space: nowrap; padding-left: 12px;">
                    <div style="display: inline-block; padding: 2px 10px; border-radius: 10px; background: {conf_badge_color}; color: #fff; font-size: 10px; font-weight: 700; margin-bottom: 6px; letter-spacing: 0.5px;">
                        {conf_badge_label}
                    </div>
                    <div style="margin-top: 4px;">{apply_link}</div>
                </td>
            </tr>
        </table>
    </div>
    """


def _format_location(job: Any) -> str:
    parts = []
    if job.is_remote:
        parts.append("Remote")
    elif job.remote_type and job.remote_type.lower() != "onsite":
        parts.append(job.remote_type.capitalize())
    if job.city:
        parts.append(job.city)
    if job.country:
        parts.append(job.country)
    elif job.location and not job.city:
        parts.append(job.location)
    return " &middot; ".join(parts) if parts else "Location N/A"


def _format_salary(salary_min: Decimal | None, salary_max: Decimal | None, currency: str | None) -> str:
    if salary_min and salary_max:
        sym = "$" if currency and currency.upper() == "USD" else (currency or "$")
        return f"{sym}{salary_min:,.0f} - {sym}{salary_max:,.0f}"
    if salary_min:
        sym = "$" if currency and currency.upper() == "USD" else (currency or "$")
        return f"From {sym}{salary_min:,.0f}"
    if salary_max:
        sym = "$" if currency and currency.upper() == "USD" else (currency or "$")
        return f"Up to {sym}{salary_max:,.0f}"
    return ""


def _format_posted(posted_at: datetime | None) -> str:
    if posted_at is None:
        return ""
    now = datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    diff = now - posted_at
    days = diff.days
    if days < 1:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago" if hours > 0 else "Just now"
    if days == 1:
        return "1 day ago"
    if days < 30:
        return f"{days} days ago"
    return posted_at.strftime("%b %d")
