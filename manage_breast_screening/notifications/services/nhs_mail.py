import os
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
from smtplib import SMTP

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
        content = (
            self.failure_report_content(todays_date)
            if report_type == "invites_not_sent"
            else self.aggregate_report_content(todays_date)
        )

        message = MIMEMultipart()

        message.attach(MIMEText(content["body"], "plain"))

        message["Subject"] = content["subject"]
        message["From"] = self._sender_email
        message["To"] = ",".join(self._recipient_emails)

        attachment = MIMEApplication(attachment_data, Name=attachment_filename)
        attachment["Content-Disposition"] = (
            f'attachment; filename="{attachment_filename}"'
        )
        message.attach(attachment)

        return message

    def failure_report_content(self, date) -> dict[str, str]:
        return {
            "subject": self._failure_report_subject_text(date),
            "body": self._failure_report_body_text(),
        }

    def _failure_report_subject_text(self, date) -> str:
        return f"Breast screening digital comms invites not sent report – {date} – Birmingham (MCR)"

    def _failure_report_body_text(self) -> str:
        return f"""Hello \n
                Please find invites not sent report attached. \n
                For any questions please email {self._sender_email}"""

    def aggregate_report_content(self, date) -> dict[str, str]:
        return {
            "subject": self._aggregate_report_subject_text(date),
            "body": self._aggregate_report_body_text(),
        }

    def _aggregate_report_subject_text(self, date) -> str:
        return f"Breast screening digital comms daily aggregate report – {date} – Birmingham (MCR)"

    def _aggregate_report_body_text(self) -> str:
        return f"""Hello \n
                Please find daily aggregate report attached. \n
                For any questions please email {self._sender_email}"""
