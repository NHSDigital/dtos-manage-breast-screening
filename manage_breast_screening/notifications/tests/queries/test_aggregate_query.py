from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import connection

from manage_breast_screening.notifications.models import Clinic
from manage_breast_screening.notifications.queries.aggregate_query import AggregateQuery
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ChannelStatusFactory,
    ClinicFactory,
    MessageFactory,
    MessageStatusFactory,
)


@pytest.mark.django_db
class TestAggregateQuery:
    def create_appointment_set(
        self,
        date: datetime,
        clinic: Clinic,
        episode_type: str,
        message_status: str,
        channel_statuses: dict[str, str],
    ):
        appt = AppointmentFactory(
            clinic=clinic,
            starts_at=date,
            episode_type=episode_type,
        )
        message = MessageFactory(appointment=appt, status=message_status)
        MessageStatusFactory(message=message, status=message_status)
        for channel, status in channel_statuses.items():
            ChannelStatusFactory(message=message, channel=channel, status=status)
        return appt

    def test_query_aggregates_appointments_and_cascade_counts(self):
        clinic1 = ClinicFactory(code="BU000", bso_code="ABC", name="BSU 1")
        clinic2 = ClinicFactory(code="BU001", bso_code="XYZ", name="BSU 2")
        date1 = datetime.today() - timedelta(days=10)
        date1.replace(tzinfo=ZoneInfo("Europe/London"))
        date2 = datetime.today() - timedelta(days=15)
        date2.replace(tzinfo=ZoneInfo("Europe/London"))

        nhsapp_read = {"nhsapp": "read"}
        sms_delivered = {"nhsapp": "unnotified", "sms": "delivered"}
        letter_sent = {
            "nhsapp": "unnotified",
            "sms": "permanent_failure",
            "letter": "received",
        }
        failed = {
            "nhsapp": "unnotified",
            "sms": "permanent_failure",
            "letter": "validation_failed",
        }

        df1 = date1.strftime("%Y-%m-%d")
        df2 = date2.strftime("%Y-%m-%d")

        test_data = [
            # Date 1
            # BU000, R, 1, 0, 0, 0, 1
            [date1, clinic1, "R", "failed", failed],
            # BU000, S, 2, 1, 1, 0, 0
            [date1, clinic1, "S", "delivered", nhsapp_read],
            [date1, clinic1, "S", "delivered", sms_delivered],
            # BU001, F, 3, 2, 1, 0, 0
            [date1, clinic2, "F", "delivered", nhsapp_read],
            [date1, clinic2, "F", "delivered", nhsapp_read],
            [date1, clinic2, "F", "delivered", sms_delivered],
            # BU001, S, 1, 1, 0, 0, 0
            [date1, clinic2, "S", "delivered", nhsapp_read],
            # Date 2
            # BU000, F, 1, 0, 0, 0, 1
            [date2, clinic1, "F", "failed", failed],
            # BU000, R, 2, 0, 0, 2, 0
            [date2, clinic1, "R", "delivered", letter_sent],
            [date2, clinic1, "R", "delivered", letter_sent],
            # BU001, F, 5, 5, 0, 0, 0
            [date2, clinic2, "F", "delivered", nhsapp_read],
            [date2, clinic2, "F", "delivered", nhsapp_read],
            [date2, clinic2, "F", "delivered", nhsapp_read],
            [date2, clinic2, "F", "delivered", nhsapp_read],
            [date2, clinic2, "F", "delivered", nhsapp_read],
        ]

        expectations = [
            [df1, "ABC", "BU000", "BSU 1", "R", 1, 0, 0, 0, 1],
            [df1, "ABC", "BU000", "BSU 1", "S", 2, 1, 1, 0, 0],
            [df1, "XYZ", "BU001", "BSU 2", "F", 3, 2, 1, 0, 0],
            [df1, "XYZ", "BU001", "BSU 2", "S", 1, 1, 0, 0, 0],
            [df2, "ABC", "BU000", "BSU 1", "F", 1, 0, 0, 0, 1],
            [df2, "ABC", "BU000", "BSU 1", "R", 2, 0, 0, 2, 0],
            [df2, "XYZ", "BU001", "BSU 2", "F", 5, 5, 0, 0, 0],
        ]

        for d in test_data:
            self.create_appointment_set(*d)

        with connection.cursor() as cursor:
            cursor.execute(AggregateQuery.sql(), ("1 month",))
            results = cursor.fetchall()

        for idx, res in enumerate(results):
            assert expectations[idx] == list(res)

    def test_aggregate_uses_date_range(self):
        over_a_week_ago = datetime.now() - timedelta(days=9)
        yesterday = datetime.now() - timedelta(days=1)
        self.create_appointment_set(
            over_a_week_ago,
            ClinicFactory(),
            "F",
            "delivered",
            {"nhsapp": "read"},
        )
        self.create_appointment_set(
            yesterday, ClinicFactory(), "F", "delivered", {"nhsapp": "read"}
        )

        with connection.cursor() as cursor:
            cursor.execute(AggregateQuery.sql(), ("1 week",))
            results = cursor.fetchall()

        assert len(results) == 1
