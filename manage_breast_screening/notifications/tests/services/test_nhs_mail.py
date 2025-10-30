import email
import smtplib
from datetime import datetime
from email.header import decode_header, make_header
from unittest.mock import ANY, MagicMock, patch

import pytest

from manage_breast_screening.notifications.models import ZONE_INFO
from manage_breast_screening.notifications.services.nhs_mail import NhsMail


@pytest.mark.time_machine(datetime(2025, 10, 11, tzinfo=ZONE_INFO))
class TestNhsMail:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATIONS_SMTP_RECIPIENTS", "recipient@nhsmail.net")
        monkeypatch.setenv("NOTIFICATIONS_SMTP_USERNAME", "sender@nhsmail.net")
        monkeypatch.setenv("NOTIFICATIONS_SMTP_PASSWORD", "password")

    @pytest.fixture()
    def mock_smtp_server(self):
        mock_smtp = MagicMock(name="mock_smtp")
        with patch(
            "manage_breast_screening.notifications.services.nhs_mail.SMTP",
            new=mock_smtp,
        ) as smtp:
            yield smtp.return_value.__enter__.return_value

    @pytest.fixture
    def csv_data(self):
        return "this,that,1,8,1,2,1"

    def test_sends_to_multiple_emails(self, mock_smtp_server, csv_data, monkeypatch):
        monkeypatch.setenv(
            "NOTIFICATIONS_SMTP_RECIPIENTS", "recipient@nhsmail.net,another@nhs.net"
        )
        subject = NhsMail()
        subject.send_report_email(csv_data, "filename.csv", "invites_not_sent")

        mock_smtp_server.login.assert_called_once_with("sender@nhsmail.net", "password")
        mock_smtp_server.sendmail.assert_called_once_with(
            "sender@nhsmail.net", ["recipient@nhsmail.net", "another@nhs.net"], ANY
        )

    def test_sends_a_failure_report_email(self, mock_smtp_server, csv_data):
        subject = NhsMail()
        subject.send_report_email(csv_data, "filename.csv", "invites_not_sent")

        mock_smtp_server.login.assert_called_once_with("sender@nhsmail.net", "password")
        mock_smtp_server.sendmail.assert_called_once_with(
            "sender@nhsmail.net", ["recipient@nhsmail.net"], ANY
        )

        email_content = mock_smtp_server.sendmail.call_args[0][2]
        mime_message = email.message_from_string(email_content)

        decoded_subject_line = str(make_header(decode_header(mime_message["Subject"])))
        assert (
            "Breast screening digital comms invites not sent report – 11-10-2025 – Birmingham (MCR)"
            in decoded_subject_line
        )
        assert "Content-Type: text/html" in email_content
        assert (
            "It's important that you take action when you receive this email"
            in email_content
        )

        assert "filename.csv" in email_content
        decoded_attachment_data = (
            mime_message.get_payload()[1]  # type: ignore
            .get_payload(  # type: ignore
                None, True
            )
            .decode("utf-8")  # type: ignore
        )
        assert csv_data in decoded_attachment_data

    def test_sends_an_aggregate_report_email(self, mock_smtp_server, csv_data):
        subject = NhsMail()
        subject.send_report_email(csv_data, "filename.csv", "aggregate")

        mock_smtp_server.login.assert_called_once_with("sender@nhsmail.net", "password")
        mock_smtp_server.sendmail.assert_called_once_with(
            "sender@nhsmail.net", ["recipient@nhsmail.net"], ANY
        )
        email_content = mock_smtp_server.sendmail.call_args[0][2]
        mime_message = email.message_from_string(email_content)

        decoded_subject_line = str(make_header(decode_header(mime_message["Subject"])))

        assert (
            "Breast screening digital comms aggregate report – 11-10-2025 – Birmingham (MCR)"
            in decoded_subject_line
        )
        assert (
            "Attached to the email is the daily report for breast screening digital"
            in email_content
        )
        assert "filename.csv" in email_content
        decoded_attachment_data = (
            mime_message.get_payload()[1]  # type: ignore
            .get_payload(  # type: ignore
                None, True
            )
            .decode("utf-8")  # type: ignore
        )
        assert csv_data in decoded_attachment_data

    def test_raises_exception_if_email_fails(self, mock_smtp_server, csv_data):
        mock_smtp_server.sendmail.side_effect = smtplib.SMTPException

        with pytest.raises(smtplib.SMTPException):
            subject = NhsMail()
            subject.send_report_email(csv_data, "filename.csv")
