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

    def send_report_email(
        self,
        attachment_data: str,
        attachment_filename: str,
        report_type="invites_not_sent",
    ):
        email = self._get_email_content(
            attachment_data, attachment_filename, report_type
        )

        logger.info(
            f"Email for report type {report_type} created with attachment {attachment_filename}"
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

    def _get_email_content(self, attachment_data, attachment_filename, report_type):
        todays_date = datetime.today().strftime("%d-%m-%Y")
        message = MIMEMultipart()

        message.attach(MIMEText(self._body(report_type), "html"))

        message["Subject"] = self._subject(report_type, todays_date)
        message["From"] = self._sender_email
        message["To"] = ",".join(self._recipient_emails)

        attachment = MIMEApplication(attachment_data, Name=attachment_filename)
        attachment["Content-Disposition"] = (
            f'attachment; filename="{attachment_filename}"'
        )
        message.attach(attachment)

        return message

    def _subject(self, report_type, date, bso="Birmingham (MCR)") -> str:
        default_subject = f"Breast screening digital comms {report_type.replace('_', ' ')} report – {date} – {bso}"
        environment = os.getenv("DJANGO_ENV", "local")
        if environment != "prod":
            return f"[{environment.upper()}] {default_subject}"
        else:
            return default_subject

    def _body(self, report_type) -> str:
        return render_to_string(f"report_emails/{report_type}.html")
