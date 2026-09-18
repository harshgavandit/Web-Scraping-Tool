import html
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.alert import Alert
from app.models.product_intelligence import IssueCluster
from app.utils.datetime_utils import utc_now


ALERT_LEVELS = {"Elevated", "Critical"}


class SMTPEmailSender:
    def send(self, recipients: list[str], subject: str, text_body: str, html_body: str) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise RuntimeError("SMTP_HOST and SMTP_FROM_EMAIL must be configured")
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = ", ".join(recipients)
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)


email_sender = SMTPEmailSender()


def _recipients() -> list[str]:
    return list(dict.fromkeys(
        value.strip() for value in settings.EMAIL_ALERT_RECIPIENTS.split(",") if value.strip()
    ))


def sync_reputation_alerts(db: Session, brand_id: int) -> list[Alert]:
    clusters = db.query(IssueCluster).filter(IssueCluster.brand_id == brand_id).all()
    alerts = []
    active_cluster_ids = set()
    for cluster in clusters:
        if cluster.risk_level not in ALERT_LEVELS:
            continue
        active_cluster_ids.add(cluster.id)
        alert = db.query(Alert).filter(
            Alert.brand_id == brand_id,
            Alert.issue_cluster_id == cluster.id,
        ).first()
        if alert is None:
            alert = Alert(brand_id=brand_id, issue_cluster_id=cluster.id)
            db.add(alert)
        if alert.severity != cluster.risk_level:
            alert.email_status = "pending"
            alert.email_error = None
        alert.severity = cluster.risk_level
        alert.title = cluster.title
        alert.message = (
            f"{cluster.mention_count} negative mentions across {cluster.unique_sources} "
            f"independent sources; volume changed {cluster.growth_pct:.0f}% in the current window."
        )
        alert.evidence_count = cluster.mention_count
        alert.updated_at = utc_now()
        alerts.append(alert)

    stale = db.query(Alert).filter(Alert.brand_id == brand_id, Alert.status == "open").all()
    for alert in stale:
        if alert.issue_cluster_id not in active_cluster_ids:
            alert.status = "resolved"
            alert.resolved_at = utc_now()
    db.flush()
    return alerts


def dispatch_email_alerts(db: Session, alerts: list[Alert], sender: SMTPEmailSender = email_sender) -> int:
    recipients = _recipients()
    if not settings.EMAIL_ALERTS_ENABLED or not recipients:
        return 0
    sent_count = 0
    for alert in alerts:
        if alert.email_status == "sent" and alert.email_severity_sent == alert.severity:
            continue
        subject = f"[{alert.severity}] Brand reputation alert: {alert.title}"
        text_body = (
            f"{alert.title}\n\n{alert.message}\n\n"
            f"Evidence mentions: {alert.evidence_count}\nReview the dashboard: {settings.APP_PUBLIC_URL}"
        )
        html_body = (
            "<h2>Brand reputation alert</h2>"
            f"<p><strong>{html.escape(alert.severity)}</strong> — {html.escape(alert.title)}</p>"
            f"<p>{html.escape(alert.message)}</p>"
            f"<p>Evidence mentions: {alert.evidence_count}</p>"
            f'<p><a href="{html.escape(settings.APP_PUBLIC_URL, quote=True)}">Review the dashboard</a></p>'
        )
        alert.email_recipients = recipients
        try:
            sender.send(recipients, subject, text_body, html_body)
            alert.email_status = "sent"
            alert.email_sent_at = utc_now()
            alert.email_severity_sent = alert.severity
            alert.email_error = None
            sent_count += 1
        except Exception as exc:
            alert.email_status = "failed"
            alert.email_error = str(exc)[:1000]
            logger.error("Reputation email alert delivery failed for alert %s: %s", alert.id, exc)
    db.flush()
    return sent_count
