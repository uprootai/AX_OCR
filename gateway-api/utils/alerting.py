"""
Error Alerting System
에러 발생 시 이메일/슬랙/웹훅으로 알림 전송

Features:
- Email notifications via SMTP
- Slack webhook integration
- Generic webhook support
- Rate limiting to prevent alert spam
- Error grouping and deduplication
"""
import os
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from collections import defaultdict
import httpx

logger = logging.getLogger(__name__)


class AlertRateLimiter:
    """
    알림 속도 제한기
    동일한 에러에 대한 알림 스팸 방지
    """

    def __init__(self, max_alerts_per_hour: int = 10):
        """
        Args:
            max_alerts_per_hour: 시간당 최대 알림 수
        """
        self.max_alerts_per_hour = max_alerts_per_hour
        self.alert_history: Dict[str, List[datetime]] = defaultdict(list)

    def should_alert(self, error_key: str) -> bool:
        """
        알림 전송 여부 판단

        Args:
            error_key: 에러 식별 키 (예: 에러 타입 + 메시지 해시)

        Returns:
            알림 전송 가능 여부
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Remove old entries
        self.alert_history[error_key] = [
            ts for ts in self.alert_history[error_key] if ts > one_hour_ago
        ]

        # Check rate limit
        if len(self.alert_history[error_key]) >= self.max_alerts_per_hour:
            logger.warning(
                f"Alert rate limit reached for error: {error_key} "
                f"({len(self.alert_history[error_key])} alerts in last hour)"
            )
            return False

        # Add current timestamp
        self.alert_history[error_key].append(now)
        return True

    def reset(self, error_key: Optional[str] = None):
        """
        알림 히스토리 리셋

        Args:
            error_key: 특정 에러 키만 리셋 (None이면 전체 리셋)
        """
        if error_key:
            self.alert_history.pop(error_key, None)
        else:
            self.alert_history.clear()


class EmailAlerter:
    """이메일 알림 발송"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True
    ):
        """
        Args:
            smtp_host: SMTP 서버 호스트
            smtp_port: SMTP 포트 (TLS: 587, SSL: 465)
            smtp_user: SMTP 사용자명
            smtp_password: SMTP 비밀번호
            from_email: 발신자 이메일
            to_emails: 수신자 이메일 리스트
            use_tls: TLS 사용 여부
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    def send_alert(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        traceback: Optional[str] = None
    ) -> bool:
        """
        에러 알림 이메일 전송

        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            context: 추가 컨텍스트 정보
            traceback: 스택 트레이스

        Returns:
            성공 여부
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Gateway API Error] {error_type}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)

            # Email body
            body = self._format_email_body(error_type, error_message, context, traceback)

            # Attach body
            msg.attach(MIMEText(body, 'html'))

            # Send email
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, self.to_emails, msg.as_string())
            server.quit()

            logger.info(f"Error alert email sent to {self.to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def _format_email_body(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]],
        traceback: Optional[str]
    ) -> str:
        """이메일 본문 HTML 포맷"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #d32f2f; color: white; padding: 15px; }}
                .content {{ padding: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .label {{ font-weight: bold; }}
                .code {{ background-color: #f5f5f5; padding: 10px; font-family: monospace; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Gateway API Error Alert</h2>
            </div>
            <div class="content">
                <div class="section">
                    <span class="label">Timestamp:</span> {timestamp}
                </div>
                <div class="section">
                    <span class="label">Error Type:</span> {error_type}
                </div>
                <div class="section">
                    <span class="label">Error Message:</span><br>
                    <div class="code">{error_message}</div>
                </div>
        """

        if context:
            html += """
                <div class="section">
                    <span class="label">Context:</span><br>
                    <div class="code">"""
            for key, value in context.items():
                html += f"{key}: {value}<br>"
            html += "</div></div>"

        if traceback:
            html += f"""
                <div class="section">
                    <span class="label">Traceback:</span><br>
                    <div class="code">{traceback}</div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html


class SlackAlerter:
    """Slack 웹훅 알림 발송"""

    def __init__(self, webhook_url: str, mention_users: Optional[List[str]] = None):
        """
        Args:
            webhook_url: Slack incoming webhook URL
            mention_users: 멘션할 사용자 ID 리스트 (예: ["U123456", "U789012"])
        """
        self.webhook_url = webhook_url
        self.mention_users = mention_users or []

    async def send_alert(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        traceback: Optional[str] = None
    ) -> bool:
        """
        에러 알림 Slack 메시지 전송

        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            context: 추가 컨텍스트 정보
            traceback: 스택 트레이스

        Returns:
            성공 여부
        """
        try:
            # Build Slack message
            blocks = self._build_slack_blocks(error_type, error_message, context, traceback)

            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={"blocks": blocks},
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info("Error alert sent to Slack")
                    return True
                else:
                    logger.error(f"Failed to send Slack alert: {response.status_code} {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def _build_slack_blocks(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]],
        traceback: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Slack 메시지 블록 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Mention users if specified
        mentions = " ".join([f"<@{user}>" for user in self.mention_users])

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Gateway API Error Alert {mentions}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Timestamp:*\n{timestamp}"},
                    {"type": "mrkdwn", "text": f"*Error Type:*\n`{error_type}`"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error Message:*\n```{error_message[:500]}```"
                }
            }
        ]

        if context:
            context_text = "\n".join([f"• *{k}:* {v}" for k, v in context.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Context:*\n{context_text}"
                }
            })

        if traceback:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Traceback:*\n```{traceback[:1000]}```"
                }
            })

        return blocks


class AlertManager:
    """
    통합 알림 관리자
    여러 알림 채널을 관리하고 rate limiting 적용
    """

    def __init__(self, rate_limiter: Optional[AlertRateLimiter] = None):
        """
        Args:
            rate_limiter: 알림 속도 제한기
        """
        self.rate_limiter = rate_limiter or AlertRateLimiter(max_alerts_per_hour=10)
        self.email_alerter: Optional[EmailAlerter] = None
        self.slack_alerter: Optional[SlackAlerter] = None

    def configure_email(self, **kwargs):
        """이메일 알림 설정"""
        self.email_alerter = EmailAlerter(**kwargs)
        logger.info("Email alerting configured")

    def configure_slack(self, **kwargs):
        """Slack 알림 설정"""
        self.slack_alerter = SlackAlerter(**kwargs)
        logger.info("Slack alerting configured")

    async def send_alert(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        traceback: Optional[str] = None,
        force: bool = False
    ):
        """
        모든 설정된 채널로 알림 전송

        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            context: 추가 컨텍스트
            traceback: 스택 트레이스
            force: rate limiting 무시
        """
        # Generate error key for rate limiting
        error_key = f"{error_type}:{hash(error_message)}"

        # Check rate limit
        if not force and not self.rate_limiter.should_alert(error_key):
            logger.info(f"Alert suppressed due to rate limiting: {error_key}")
            return

        # Send to all configured channels
        if self.email_alerter:
            try:
                self.email_alerter.send_alert(error_type, error_message, context, traceback)
            except Exception as e:
                logger.error(f"Email alert failed: {e}")

        if self.slack_alerter:
            try:
                await self.slack_alerter.send_alert(error_type, error_message, context, traceback)
            except Exception as e:
                logger.error(f"Slack alert failed: {e}")


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """글로벌 AlertManager 인스턴스 반환"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def setup_alerting_from_env():
    """
    환경 변수에서 알림 설정 로드

    Environment variables:
        ALERT_EMAIL_ENABLED: 이메일 알림 활성화 (true/false)
        ALERT_SMTP_HOST: SMTP 서버 호스트
        ALERT_SMTP_PORT: SMTP 포트
        ALERT_SMTP_USER: SMTP 사용자명
        ALERT_SMTP_PASSWORD: SMTP 비밀번호
        ALERT_FROM_EMAIL: 발신자 이메일
        ALERT_TO_EMAILS: 수신자 이메일 (콤마로 구분)

        ALERT_SLACK_ENABLED: Slack 알림 활성화 (true/false)
        ALERT_SLACK_WEBHOOK_URL: Slack webhook URL
        ALERT_SLACK_MENTION_USERS: 멘션할 사용자 ID (콤마로 구분)

        ALERT_RATE_LIMIT: 시간당 최대 알림 수 (기본: 10)
    """
    manager = get_alert_manager()

    # Configure rate limiter
    rate_limit = int(os.getenv("ALERT_RATE_LIMIT", "10"))
    manager.rate_limiter = AlertRateLimiter(max_alerts_per_hour=rate_limit)

    # Configure email
    if os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true":
        to_emails = os.getenv("ALERT_TO_EMAILS", "").split(",")
        to_emails = [email.strip() for email in to_emails if email.strip()]

        if to_emails:
            manager.configure_email(
                smtp_host=os.getenv("ALERT_SMTP_HOST", "localhost"),
                smtp_port=int(os.getenv("ALERT_SMTP_PORT", "587")),
                smtp_user=os.getenv("ALERT_SMTP_USER", ""),
                smtp_password=os.getenv("ALERT_SMTP_PASSWORD", ""),
                from_email=os.getenv("ALERT_FROM_EMAIL", "alerts@example.com"),
                to_emails=to_emails,
                use_tls=os.getenv("ALERT_SMTP_USE_TLS", "true").lower() == "true"
            )
            logger.info(f"Email alerting enabled (to: {to_emails})")

    # Configure Slack
    if os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true":
        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")

        if webhook_url:
            mention_users = os.getenv("ALERT_SLACK_MENTION_USERS", "").split(",")
            mention_users = [user.strip() for user in mention_users if user.strip()]

            manager.configure_slack(
                webhook_url=webhook_url,
                mention_users=mention_users
            )
            logger.info("Slack alerting enabled")

    return manager


__all__ = [
    'AlertManager',
    'EmailAlerter',
    'SlackAlerter',
    'AlertRateLimiter',
    'get_alert_manager',
    'setup_alerting_from_env'
]
