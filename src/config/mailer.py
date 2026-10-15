import asyncio
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List
from src.config.settings import settings

logger = logging.getLogger("mailer")


class GmailSMTPMailer:
    """
    Mailer Service menggunakan protokol SMTP Gmail (TLS Port 587).
    Menggunakan asyncio.to_thread agar non-blocking pada event loop FastAPI.
    """

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.MAIL_FROM or settings.SMTP_USER
        self.from_name = settings.MAIL_FROM_NAME

    def _send_sync(self, msg: MIMEMultipart, recipients: List[str]):
        """Eksekusi pengiriman email sinkron ke server SMTP Gmail."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20.0) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, recipients, msg.as_string())

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Mengirim email HTML (dengan fallback plain text) secara asinkron.
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP_USER atau SMTP_PASSWORD belum dikonfigurasi. Email dilewati.")
            return False

        recipients = [to_email] if isinstance(to_email, str) else to_email

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = ", ".join(recipients)

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            await asyncio.to_thread(self._send_sync, msg, recipients)
            logger.info(f"Email berhasil dikirim ke: {recipients}")
            return True
        except Exception as e:
            logger.error(f"Gagal mengirim email ke {recipients}: {str(e)}")
            return False


mailer = GmailSMTPMailer()
