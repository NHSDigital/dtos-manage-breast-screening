from datetime import datetime, timedelta
from random import randrange
from zoneinfo import ZoneInfo

import pytest

from manage_breast_screening.notifications.queries.failures_query import FailuresQuery
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    MessageFactory,
    MessageStatusFactory,
)


class TestFailuresQuery:
    def create_message_set(
        self,
        date: datetime,
        nhs_number: str,
        episode_type: str,
        status: str,
        description: str,
    ):
        appt = AppointmentFactory(
            starts_at=date, nhs_number=nhs_number, episode_type=episode_type
        )
        message = MessageFactory(appointment=appt)
        MessageStatusFactory(message=message, status=status, description=description)
        return appt

    @pytest.mark.django_db
    def test_failures_query_data_today(self):
        def is_today(date_and_time: datetime) -> bool:
            return date_and_time.strftime("%Y-%m-%d") == datetime.today().strftime(
                "%Y-%m-%d"
            )

        def sometime_today():
            now = datetime.today()
            today = now.replace(hour=0, minute=0, tzinfo=ZoneInfo("Europe/London"))
            return today + timedelta(hours=randrange(24), minutes=randrange(60))

        appt1 = self.create_message_set(
            sometime_today(),
            "9990001111",
            "S",
            "failed",
            "No reachable communication channel",
        )
        appt2 = self.create_message_set(
            sometime_today(), "9990001112", "F", "failed", "Patient has an exit code"
        )
        appt3 = self.create_message_set(
            sometime_today(), "9990001113", "R", "failed", "Patient is formally dead"
        )
        appt4 = self.create_message_set(
            sometime_today(), "9990001114", "R", "failed", "Patient is informally dead"
        )
        appt5 = self.create_message_set(
            sometime_today(),
            "9990001115",
            "S",
            "failed",
            "No reachable communication channel",
        )

        self.create_message_set(
            sometime_today(), "9990001116", "S", "delivered", "Delivered"
        )
        self.create_message_set(
            sometime_today() - timedelta(days=2),
            "9990001117",
            "S",
            "failed",
            "No reachable communication channel",
        )
        today_formatted = datetime.today().strftime("%Y-%m-%d")

        results = FailuresQuery.query()

        assert len(results) == 5

        assert results[0]["nhs_number"] == 9990001111
        assert results[0]["appointment_date"] == appt1.starts_at
        assert results[0]["episode_type"] == "Self referral"
        assert results[0]["clinic_code"] == appt1.clinic.code
        assert results[0]["failure_date"] == today_formatted
        assert results[0]["failure_reason"] == "No reachable communication channel"

        assert results[1]["nhs_number"] == 9990001112
        assert results[1]["appointment_date"] == appt2.starts_at
        assert results[1]["episode_type"] == "Routine first call"
        assert results[1]["clinic_code"] == appt2.clinic.code
        assert results[1]["failure_date"] == today_formatted
        assert results[1]["failure_reason"] == "Patient has an exit code"

        assert results[2]["nhs_number"] == 9990001113
        assert results[2]["appointment_date"] == appt3.starts_at
        assert results[2]["episode_type"] == "Routine recall"
        assert results[2]["clinic_code"] == appt3.clinic.code
        assert results[2]["failure_date"] == today_formatted
        assert results[2]["failure_reason"] == "Patient is formally dead"

        assert results[3]["nhs_number"] == 9990001114
        assert results[3]["appointment_date"] == appt4.starts_at
        assert results[3]["episode_type"] == "Routine recall"
        assert results[3]["clinic_code"] == appt4.clinic.code
        assert results[3]["failure_date"] == today_formatted
        assert results[3]["failure_reason"] == "Patient is informally dead"

        assert results[4]["nhs_number"] == 9990001115
        assert results[4]["appointment_date"] == appt5.starts_at
        assert results[4]["episode_type"] == "Self referral"
        assert results[4]["clinic_code"] == appt5.clinic.code
        assert results[4]["failure_date"] == today_formatted
        assert results[4]["failure_reason"] == "No reachable communication channel"

    @pytest.mark.django_db
    def test_failures_query_for_given_date(self):
        the_date = datetime.today() - timedelta(days=2)

        self.create_message_set(
            the_date, "9990001111", "S", "failed", "No reachable communication channel"
        )
        self.create_message_set(
            the_date - timedelta(days=1),
            "9990001112",
            "R",
            "failed",
            "No reachable communication channel",
        )

        results = FailuresQuery.query(the_date)

        assert len(results) == 1
        assert results[0]["nhs_number"] == 9990001111

    def test_failures_query_columns(self):
        assert FailuresQuery.columns() == [
            "NHS number",
            "Appointment date",
            "Clinic code",
            "Episode type",
            "Failure date",
            "Failure reason",
        ]

    def test_failures_query_sql(self):
        assert 'SELECT "notifications_appointment"."nhs_number"' in FailuresQuery.sql()
