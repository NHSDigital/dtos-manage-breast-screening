from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import connection

from manage_breast_screening.notifications.models import Clinic
from manage_breast_screening.notifications.queries.helper import Helper
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
        message = MessageFactory(
            appointment=appt, status=message_status, sent_at=datetime.now()
        )
        MessageStatusFactory(
            message=message, status=message_status, status_updated_at=datetime.now()
        )
        for channel, status in channel_statuses.items():
            ChannelStatusFactory(
                message=message,
                channel=channel,
                status=status,
                status_updated_at=datetime.now(),
            )
        return appt

    def test_query_aggregates_appointments_and_cascade_counts(self):
        now = datetime.now(tz=ZoneInfo("Europe/London"))
        clinic1 = ClinicFactory(code="BU001", bso_code="BSO1", name="BSU 1")
        clinic2 = ClinicFactory(code="BU002", bso_code="BSO2", name="BSU 2")

        date1 = now - timedelta(days=10)
        df1 = date1.strftime("%Y-%m-%d")

        date2 = now - timedelta(days=15)
        df2 = date2.strftime("%Y-%m-%d")

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
            [df1, "BSO1", "BU001", "BSU 1", "Routine recall", 1, 0, 0, 0, 1],
            [df1, "BSO1", "BU001", "BSU 1", "Self referral", 2, 1, 1, 0, 0],
            [df1, "BSO2", "BU002", "BSU 2", "Routine first call", 3, 2, 1, 0, 0],
            [df1, "BSO2", "BU002", "BSU 2", "Self referral", 1, 1, 0, 0, 0],
            [df2, "BSO1", "BU001", "BSU 1", "Routine first call", 1, 0, 0, 0, 1],
            [df2, "BSO1", "BU001", "BSU 1", "Routine recall", 2, 0, 0, 2, 0],
            [df2, "BSO2", "BU002", "BSU 2", "Routine first call", 5, 5, 0, 0, 0],
        ]

        for d in test_data:
            self.create_appointment_set(*d)

        with connection.cursor() as cursor:
            cursor.execute(Helper.sql("aggregate"), ("1 month",))
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
            cursor.execute(Helper.sql("aggregate"), ("1 week",))
            results = cursor.fetchall()

        assert len(results) == 1

    def test_aggregate_cascade_overlaps_are_counted_once(self):
        appt_date = datetime.now() - timedelta(days=20)
        message_sent_at = datetime.now() - timedelta(days=6)
        appt = AppointmentFactory(
            clinic=ClinicFactory(code="BU006", bso_code="BSO6", name="BSU 6"),
            starts_at=appt_date,
            episode_type="S",
        )
        message = MessageFactory(
            appointment=appt, status="delivered", sent_at=message_sent_at
        )
        MessageStatusFactory(message=message, status="delivered")
        ChannelStatusFactory(
            message=message,
            channel="nhsapp",
            status="read",
            status_updated_at=(message_sent_at + timedelta(days=2)),
        )
        sms_status = ChannelStatusFactory(
            message=message,
            channel="sms",
            status="delivered",
            status_updated_at=(message_sent_at + timedelta(days=4)),
        )

        with connection.cursor() as cursor:
            cursor.execute(Helper.sql("aggregate"), ("1 month",))
            results = cursor.fetchall()

        assert list(results[0]) == [
            appt_date.strftime("%Y-%m-%d"),
            "BSO6",
            "BU006",
            "BSU 6",
            "Self referral",
            1,
            0,
            1,
            0,
            0,
        ]

        sms_status.status_updated_at = message_sent_at + timedelta(days=5)
        sms_status.save()
        ChannelStatusFactory(
            message=message,
            channel="letter",
            status="received",
            status_updated_at=(message_sent_at + timedelta(days=5)),
        )

        with connection.cursor() as cursor:
            cursor.execute(Helper.sql("aggregate"), ("1 month",))
            results = cursor.fetchall()

        assert list(results[0]) == [
            appt_date.strftime("%Y-%m-%d"),
            "BSO6",
            "BU006",
            "BSU 6",
            "Self referral",
            1,
            0,
            0,
            1,
            0,
        ]

    @pytest.mark.django_db
    def test_aggregate_columns(self):
        with connection.cursor() as cursor:
            cursor.execute(Helper.sql("aggregate") + "\nLIMIT 0", ("1 month",))
            columns = [col[0] for col in cursor.description]

        assert columns == [
            "Appointment date",
            "BSO code",
            "Clinic code",
            "Clinic name",
            "Episode type",
            "Notifications sent",
            "NHS app messages read",
            "SMS messages delivered",
            "Letters sent",
            "Notifications failed",
        ]
