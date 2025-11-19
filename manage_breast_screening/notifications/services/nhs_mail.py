import os
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
from smtplib import SMTP

from django.template.loader import render_to_string

from manage_breast_screening.config.settings import boolean_env

logger = getLogger(__name__)

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587


class NhsMail:
    def __init__(self) -> None:
        self._recipient_emails = os.getenv("NOTIFICATIONS_SMTP_RECIPIENTS", "").split(
            ","
        )
        self._sender_email = os.getenv("NOTIFICATIONS_SMTP_USERNAME", "")
        self._sender_password = os.getenv("NOTIFICATIONS_SMTP_PASSWORD", "")

    def send_reports_email(
        self,
        attachments_data: dict[str, str],
    ):
        email = self._get_email_content(attachments_data)

        logger.info(
            f"Email for reports {', '.join(attachments_data.keys())} created and sent"
        )

        if boolean_env("NOTIFICATIONS_SMTP_IS_ENABLED", False):
            self._send_via_smtp(email)
        else:
            logger.info("SMTP connection is not enabled")

    def _send_via_smtp(self, email):
        try:
            with SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(
                    self._sender_email,
                    self._sender_password,
                )

                server.sendmail(
                    email["from"], self._recipient_emails, email.as_string()
                )
        except Exception as e:
            logger.warning(
                f"Error sending email: {e}",
            )
            raise e
        else:
            logger.info("Email sent")

    def _get_email_content(self, attachments):
        todays_date = datetime.today().strftime("%d-%m-%Y")
        message = MIMEMultipart()

        message.attach(MIMEText(self._body(), "html"))

        message["Subject"] = self._subject(todays_date)
        message["From"] = self._sender_email
        message["To"] = ",".join(self._recipient_emails)

        for filename, data in attachments.items():
            attachment = MIMEApplication(data, Name=filename)
            attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
            message.attach(attachment)

        return message

    def _subject(self, date, bso="Birmingham (MCR)") -> str:
        default_subject = f"Breast screening digital comms reports – {date} – {bso}"
        environment = os.getenv("DJANGO_ENV", "local")
        if environment != "prod":
            return f"[{environment.upper()}] {default_subject}"
        else:
            return default_subject

    def _body(self) -> str:
        return render_to_string("report_emails/reports.html")
