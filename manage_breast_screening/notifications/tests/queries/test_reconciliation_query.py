from collections import namedtuple
from datetime import datetime, timedelta

import pytest
import time_machine

from manage_breast_screening.notifications.models import ZONE_INFO, Clinic
from manage_breast_screening.notifications.queries.helper import Helper
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ChannelStatusFactory,
    ClinicFactory,
    MessageFactory,
)


def formatted(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M")


def days_time(days: int):
    return datetime.now(tz=ZONE_INFO) + timedelta(days=days)


def create_appointment_set(
    nhs_number: str,
    date: datetime,
    clinic: Clinic,
    appointment_status: str,
    episode_type: str,
    message_status: str | None = None,
    channel_statuses: dict[str, str] | None = None,
):
    now = datetime.now(tz=ZONE_INFO)
    appt = AppointmentFactory(
        clinic=clinic,
        status=appointment_status,
        episode_type=episode_type,
        nhs_number=nhs_number,
        starts_at=date,
    )
    if appointment_status == "C":
        appt.cancelled_at = now
        appt.save()

    if message_status:
        message = MessageFactory(appointment=appt, status=message_status, sent_at=now)
        for channel, status in channel_statuses.items():
            ChannelStatusFactory(
                message=message,
                channel=channel,
                status=status,
                status_updated_at=now,
            )
    return appt


ResultRow = namedtuple(
    "ResultRow",
    [
        "nhs_number",
        "clinic",
        "episode_type",
        "status",
        "message_status",
        "created_at",
        "appointment_starts_at",
        "cancelled_at",
        "message_sent_at",
        "nhs_app_read_at",
        "sms_delivered_at",
        "letter_sent_at",
    ],
)


@pytest.mark.django_db
class TestReconciliationQuery:
    @pytest.fixture(autouse=True)
    def setup(self):
        clinic1 = ClinicFactory(code="BU001", bso_code="BSO1", name="BSU 1")
        clinic2 = ClinicFactory(code="BU002", bso_code="BSO1", name="BSU 2")

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
            ["9991112211", days_time(4), clinic1, "B", "R"],
            ["9991112214", days_time(6), clinic2, "C", "G"],
            ["9991112221", days_time(5), clinic2, "B", "R", "failed", failed],
            ["9991112222", days_time(6), clinic1, "B", "S", "delivered", nhsapp_read],
            ["9991112223", days_time(5), clinic2, "B", "S", "delivered", sms_delivered],
            ["9991112229", days_time(5), clinic1, "B", "R", "delivered", letter_sent],
            ["9991112252", days_time(6), clinic2, "C", "S", "delivered", nhsapp_read],
        ]

        for d in test_data:
            create_appointment_set(*d)

    @time_machine.travel(datetime.now(tz=ZONE_INFO), tick=False)
    def test_appointments_with_various_delivery_states(self):
        now = datetime.now(tz=ZONE_INFO)
        results = Helper.fetchall("reconciliation", ["1 week", "BSO1"])

        r = ResultRow(*results[0])
        assert r.nhs_number == "9991112211"
        assert r.clinic == "BSU 1 (BU001)"
        assert r.episode_type == "Routine recall"
        assert r.status == "Booked"
        assert r.message_status == "Pending"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(4))
        assert r.cancelled_at is None
        assert r.message_sent_at is None
        assert r.nhs_app_read_at is None
        assert r.sms_delivered_at is None
        assert r.letter_sent_at is None

        r = ResultRow(*results[1])
        assert r.nhs_number == "9991112214"
        assert r.clinic == "BSU 2 (BU002)"
        assert r.episode_type == "GP Referral"
        assert r.status == "Cancelled"
        assert r.message_status == "Pending"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(6))
        assert r.cancelled_at == formatted(now)
        assert r.message_sent_at is None
        assert r.nhs_app_read_at is None
        assert r.sms_delivered_at is None
        assert r.letter_sent_at is None

        r = ResultRow(*results[2])
        assert r.nhs_number == "9991112221"
        assert r.clinic == "BSU 2 (BU002)"
        assert r.episode_type == "Routine recall"
        assert r.status == "Booked"
        assert r.message_status == "Failed"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(5))
        assert r.cancelled_at is None
        assert r.message_sent_at == formatted(now)
        assert r.nhs_app_read_at is None
        assert r.sms_delivered_at is None
        assert r.letter_sent_at is None

        r = ResultRow(*results[3])
        assert r.nhs_number == "9991112222"
        assert r.clinic == "BSU 1 (BU001)"
        assert r.episode_type == "Self referral"
        assert r.status == "Booked"
        assert r.message_status == "Notified"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(6))
        assert r.cancelled_at is None
        assert r.message_sent_at == formatted(now)
        assert r.nhs_app_read_at == formatted(now)
        assert r.sms_delivered_at is None
        assert r.letter_sent_at is None

        r = ResultRow(*results[4])
        assert r.nhs_number == "9991112223"
        assert r.clinic == "BSU 2 (BU002)"
        assert r.episode_type == "Self referral"
        assert r.status == "Booked"
        assert r.message_status == "Notified"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(5))
        assert r.cancelled_at is None
        assert r.message_sent_at == formatted(now)
        assert r.nhs_app_read_at is None
        assert r.sms_delivered_at == formatted(now)
        assert r.letter_sent_at is None

        r = ResultRow(*results[5])
        assert r.nhs_number == "9991112229"
        assert r.clinic == "BSU 1 (BU001)"
        assert r.episode_type == "Routine recall"
        assert r.status == "Booked"
        assert r.message_status == "Notified"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(5))
        assert r.cancelled_at is None
        assert r.message_sent_at == formatted(now)
        assert r.nhs_app_read_at is None
        assert r.sms_delivered_at is None
        assert r.letter_sent_at == formatted(now)

        r = ResultRow(*results[6])
        assert r.nhs_number == "9991112252"
        assert r.clinic == "BSU 2 (BU002)"
        assert r.episode_type == "Self referral"
        assert r.status == "Cancelled"
        assert r.message_status == "Notified"
        assert r.created_at == formatted(now)
        assert r.appointment_starts_at == formatted(days_time(6))
        assert r.cancelled_at == formatted(now)
        assert r.message_sent_at == formatted(now)
        assert r.nhs_app_read_at == formatted(now)
        assert r.sms_delivered_at is None
        assert r.letter_sent_at is None

    def test_appointments_filtered_for_specified_bso(self):
        clinic1 = ClinicFactory(bso_code="MDB", name="Breast Care Unit", code="BU001")
        clinic2 = ClinicFactory(bso_code="WAT", code="BU002")
        AppointmentFactory.create_batch(size=2, clinic=clinic1)
        AppointmentFactory.create_batch(size=2, clinic=clinic2)

        results = Helper.fetchall("reconciliation", ["1 week", "MDB"])
        assert len(results) == 2
        assert ResultRow(*results[0]).clinic == "Breast Care Unit (BU001)"
