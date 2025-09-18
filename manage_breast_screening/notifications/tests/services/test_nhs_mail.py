import base64
import email
import smtplib
from datetime import datetime
from email.header import decode_header
from unittest.mock import ANY, MagicMock, patch

import pytest

from manage_breast_screening.notifications.management.commands.send_message_batch import (
    TZ_INFO,
)
from manage_breast_screening.notifications.services.nhs_mail import NhsMail


@pytest.mark.time_machine(datetime(2025, 10, 11, tzinfo=TZ_INFO))
class TestNhsMail:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATIONS_SMTP_RECIPIENT", "recipient@nhsmail.net")
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

    def test_sends_a_failure_report_email(self, mock_smtp_server, csv_data):
        subject = NhsMail()
        subject.send_report_email(csv_data, "filename.csv", "failures")

        mock_smtp_server.login.assert_called_once_with("sender@nhsmail.net", "password")
        mock_smtp_server.sendmail.assert_called_once_with(
            "sender@nhsmail.net", "recipient@nhsmail.net", ANY
        )
        email_content = mock_smtp_server.sendmail.call_args[0][2]

        decoded_email = email.message_from_string(email_content)
        decoded_subject_line = decode_header(decoded_email["Subject"])[0][0].decode(
            "utf-8"
        )
        assert (
            "Breast screening digital comms failure report – 11-10-2025 – Birmingham (MCR)"
            in decoded_subject_line
        )
        assert "Please find failure report attached." in email_content
        assert "filename.csv" in email_content
        decoded_attachment_data = base64.b64encode(csv_data.encode("utf-8")).decode(
            "utf-8"
        )
        assert decoded_attachment_data in email_content

    def test_sends_an_aggregate_report_email(self, mock_smtp_server, csv_data):
        subject = NhsMail()
        subject.send_report_email(csv_data, "filename.csv", "aggregate")

        mock_smtp_server.login.assert_called_once_with("sender@nhsmail.net", "password")
        mock_smtp_server.sendmail.assert_called_once_with(
            "sender@nhsmail.net", "recipient@nhsmail.net", ANY
        )
        email_content = mock_smtp_server.sendmail.call_args[0][2]

        decoded_email = email.message_from_string(email_content)
        decoded_subject_line = decode_header(decoded_email["Subject"])[0][0].decode(
            "utf-8"
        )

        assert (
            "Breast screening digital comms daily aggregate report – 11-10-2025 – Birmingham (MCR)"
            in decoded_subject_line
        )
        assert "Please find failure report attached." not in email_content
        assert "Please find daily report attached." in email_content
        assert "filename.csv" in email_content
        decoded_attachment_data = base64.b64encode(csv_data.encode("utf-8")).decode(
            "utf-8"
        )
        assert decoded_attachment_data in email_content

    def test_raises_exception_if_email_fails(self, mock_smtp_server, csv_data):
        mock_smtp_server.sendmail.side_effect = smtplib.SMTPException

        with pytest.raises(smtplib.SMTPException):
            subject = NhsMail()
            subject.send_report_email(csv_data, "filename.csv")
