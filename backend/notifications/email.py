"""Email notification sender.

Uses SMTP to deliver job alerts and notifications.  Configuration
comes from environment variables (``SMTP_HOST``, ``SMTP_PORT``, etc.).
Falls back gracefully when not configured.
"""

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config.settings import get_settings

logger = logging.getLogger("job_hunting.notifications.email")


class EmailNotifier:
    """Async-compatible email sender via SMTP."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._host = os.getenv("SMTP_HOST", "")
        self._port = int(os.getenv("SMTP_PORT", "587"))
        self._user = os.getenv("SMTP_USER", "")
        self._password = os.getenv("SMTP_PASSWORD", "")
        self._from = os.getenv("SMTP_FROM", "notifications@jobhunting.ai")

    @property
    def is_configured(self) -> bool:
        return bool(self._host and self._user and self._password)

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        *,
        html: bool = True,
    ) -> bool:
        if not self.is_configured:
            logger.debug("Email not configured — skipping")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if html else "plain"))

        try:
            import smtplib
            from email.utils import formataddr

            msg["From"] = formataddr(("Job Hunting AI", self._from))

            with smtplib.SMTP(self._host, self._port, timeout=10) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.send_message(msg)

            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to)
            return False

    async def send_job_alert(
        self,
        to: str,
        title: str,
        company: str,
        location: str,
        url: str,
        *,
        skills: list[str] | None = None,
        salary: str | None = None,
    ) -> bool:
        skills_html = f"<p><strong>Skills:</strong> {', '.join(skills)}</p>" if skills else ""
        salary_html = f"<p><strong>Salary:</strong> {salary}</p>" if salary else ""

        body = f"""
        <html><body>
        <h2>{title}</h2>
        <p><strong>{company}</strong> — {location}</p>
        {salary_html}
        {skills_html}
        <p><a href="{url}">View Job &rarr;</a></p>
        <hr>
        <p style="color:#888;font-size:12px">
            Sent by Job Hunting AI. <a href="#">Manage preferences</a>.
        </p>
        </body></html>
        """
        return await self.send(to, f"New Job: {title} at {company}", body)
