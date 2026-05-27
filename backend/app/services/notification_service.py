from __future__ import annotations

import httpx
from app.core.config import settings
from app.utils.logger import logger

SEVERITY_EMOJI = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}


async def send_slack_notification(incident_id: int, title: str, severity: str, description: str) -> None:
    if not settings.SLACK_WEBHOOK_URL:
        return
    emoji = SEVERITY_EMOJI.get(severity, "⚪")
    payload = {
        "text": f"{emoji} *New {severity} Incident* — OpsPilot AI",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {severity} Incident — OpsPilot AI"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*#{incident_id}*\n{title}"},
                {"type": "mrkdwn", "text": f"*Severity*\n{severity}"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Description*\n{description[:300]}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*View*\n{settings.FRONTEND_URL}/incidents/{incident_id}"}},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            logger.info("Slack notification sent for incident #%d", incident_id)
    except Exception as exc:
        logger.warning("Slack notification failed (non-fatal): %s", exc)


async def send_email_notification(incident_id: int, title: str, severity: str, description: str, remediation: str) -> None:
    if not settings.SENDGRID_API_KEY or not settings.ALERT_EMAIL_TO:
        return
    emoji = SEVERITY_EMOJI.get(severity, "⚪")
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0a;color:#fff;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(to right,#33ff88,#00c3ff);padding:20px 28px;">
        <h1 style="margin:0;font-size:22px;color:#000;">OpsPilot AI — {emoji} {severity} Incident</h1>
      </div>
      <div style="padding:28px;">
        <h2 style="color:#33ff88;margin-top:0;">#{incident_id}: {title}</h2>
        <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
          <tr><td style="color:#888;padding:6px 0;width:120px;">Severity</td><td style="color:#fff;font-weight:bold;">{severity}</td></tr>
          <tr><td style="color:#888;padding:6px 0;">Incident ID</td><td style="color:#fff;">#{incident_id}</td></tr>
        </table>
        <h3 style="color:#aaa;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Description</h3>
        <p style="color:#ccc;line-height:1.6;">{description}</p>
        <h3 style="color:#aaa;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Remediation</h3>
        <p style="color:#ccc;line-height:1.6;white-space:pre-line;">{remediation}</p>
        <a href="{settings.FRONTEND_URL}/incidents/{incident_id}"
           style="display:inline-block;margin-top:16px;padding:12px 24px;background:linear-gradient(to right,#33ff88,#00c3ff);color:#000;font-weight:bold;text-decoration:none;border-radius:8px;">
          View Incident →
        </a>
      </div>
      <div style="padding:16px 28px;border-top:1px solid #222;color:#555;font-size:12px;">
        OpsPilot AI · Automated incident alert
      </div>
    </div>
    """
    payload = {
        "personalizations": [{"to": [{"email": settings.ALERT_EMAIL_TO}]}],
        "from": {"email": settings.ALERT_EMAIL_FROM, "name": "OpsPilot AI"},
        "subject": f"{emoji} [{severity}] Incident #{incident_id}: {title}",
        "content": [{"type": "text/html", "value": html_body}],
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}", "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            logger.info("Email notification sent for incident #%d to %s", incident_id, settings.ALERT_EMAIL_TO)
    except Exception as exc:
        logger.warning("Email notification failed (non-fatal): %s", exc)


async def notify_all(incident_id: int, title: str, severity: str, description: str, remediation: str = "") -> None:
    """Fire both Slack and email — call this from incident creation."""
    import asyncio
    await asyncio.gather(
        send_slack_notification(incident_id, title, severity, description),
        send_email_notification(incident_id, title, severity, description, remediation),
    )
