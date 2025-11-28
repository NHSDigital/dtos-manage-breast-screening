from datetime import datetime, timedelta

import pytest
import time_machine
from django.db import connection

from manage_breast_screening.notifications.models import ZONE_INFO
from manage_breast_screening.notifications.queries.helper import Helper
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ClinicFactory,
    MessageFactory,
    MessageStatusFactory,
)


class TestFailuresQuery:
    def create_message_set(
        self,
        appt_params: dict,
        message_params: dict,
        message_status_params: dict = None,
    ):
        clinic = ClinicFactory(bso_code="BSO1", code="BSU1")
        appt = AppointmentFactory(clinic=clinic, **appt_params)
        message_params["sent_at"] = datetime.now(tz=ZONE_INFO) - timedelta(minutes=5)
        message = MessageFactory(appointment=appt, **message_params)
        if message_status_params:
            message_status_params["status_updated_at"] = datetime.now(
                tz=ZONE_INFO
            ) - timedelta(minutes=7)
            MessageStatusFactory(message=message, **message_status_params)

        return appt

    @time_machine.travel(datetime.now(tz=ZONE_INFO), tick=False)
    @pytest.mark.django_db
    def test_failures_query_data_today(self):
        appt_time = datetime.now(tz=ZONE_INFO)
        appt1 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001111", "episode_type": "S"},
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )
        appt2 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001112", "episode_type": "F"},
            {"status": "failed"},
            {"status": "failed", "description": "Patient has an exit code"},
        )
        appt3 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001113", "episode_type": "R"},
            {"status": "failed"},
            {"status": "failed", "description": "Patient is formally dead"},
        )
        appt4 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001114", "episode_type": "R"},
            {"status": "failed"},
            {"status": "failed", "description": "Patient is informally dead"},
        )
        appt5 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001115", "episode_type": "S"},
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )
        appt6 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001116", "episode_type": "S"},
            {
                "status": "failed",
                "nhs_notify_errors": [
                    {"code": "CM_INVALID_NHS_NUMBER", "title": "Invalid NHS number"}
                ],
            },
        )
        appt7 = self.create_message_set(
            {"starts_at": appt_time, "nhs_number": "9990001117", "episode_type": "S"},
            {
                "status": "failed",
                "nhs_notify_errors": [
                    {"code": "CM_INVALID_VALUE", "title": "Invalid value"},
                    {"code": "CM_INVALID_NHS_NUMBER", "title": "Invalid NHS number"},
                    {"code": "CM_MISSING_VALUE", "title": "Address inline is missing"},
                    {"code": "CM_NULL_VALUE", "title": "Clinic location is null"},
                ],
            },
        )
        self.create_message_set(
            {
                "starts_at": appt_time - timedelta(days=2),
                "nhs_number": "9990001118",
                "episode_type": "S",
            },
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )

        clinic = ClinicFactory(bso_code="BSO1", code="BSU1")

        appt8 = AppointmentFactory(
            clinic=clinic,
            starts_at=appt_time,
            nhs_number="9990001119",
            episode_type="T",
        )
        appt9 = AppointmentFactory(
            clinic=clinic, starts_at=appt_time, nhs_number="9990001120", number="2"
        )
        today_formatted = datetime.now(tz=ZONE_INFO).strftime("%Y-%m-%d")

        results = Helper.fetchall(
            "failures", [datetime.now(tz=ZONE_INFO).date(), "BSO1"]
        )

        assert len(results) == 7

        expectations = [
            [
                9990001111,
                appt1.starts_at.strftime("%Y-%m-%d"),
                appt1.clinic.code,
                "Self referral",
                today_formatted,
                "No reachable communication channel",
            ],
            [
                9990001112,
                appt2.starts_at.strftime("%Y-%m-%d"),
                appt2.clinic.code,
                "Routine first call",
                today_formatted,
                "Patient has an exit code",
            ],
            [
                9990001113,
                appt3.starts_at.strftime("%Y-%m-%d"),
                appt3.clinic.code,
                "Routine recall",
                today_formatted,
                "Patient is formally dead",
            ],
            [
                9990001114,
                appt4.starts_at.strftime("%Y-%m-%d"),
                appt4.clinic.code,
                "Routine recall",
                today_formatted,
                "Patient is informally dead",
            ],
            [
                9990001115,
                appt5.starts_at.strftime("%Y-%m-%d"),
                appt5.clinic.code,
                "Self referral",
                today_formatted,
                "No reachable communication channel",
            ],
            [
                9990001116,
                appt6.starts_at.strftime("%Y-%m-%d"),
                appt6.clinic.code,
                "Self referral",
                today_formatted,
                "Invalid NHS number",
            ],
            [
                9990001117,
                appt7.starts_at.strftime("%Y-%m-%d"),
                appt7.clinic.code,
                "Self referral",
                today_formatted,
                "Invalid value, Invalid NHS number, Address inline is missing, Clinic location is null",
            ],
            [
                9990001119,
                appt8.starts_at.strftime("%Y-%m-%d"),
                appt8.clinic.code,
                "VHR early recall",
                today_formatted,
                "Invitation not sent as episode type is not supported",
            ],
            [
                9990001120,
                appt9.starts_at.strftime("%Y-%m-%d"),
                appt9.clinic.code,
                "Self referral",
                today_formatted,
                "Invitation not sent as not a 1st time appointment",
            ],
        ]

        for idx, res in enumerate(results):
            assert expectations[idx] == list(res)

    @time_machine.travel(datetime.now(tz=ZONE_INFO), tick=False)
    @pytest.mark.django_db
    def test_failures_query_for_given_date(self):
        the_date = datetime.now(tz=ZONE_INFO) - timedelta(days=2)
        self.create_message_set(
            {"starts_at": the_date, "nhs_number": "9990001111", "episode_type": "S"},
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )
        self.create_message_set(
            {
                "starts_at": the_date - timedelta(days=1),
                "nhs_number": "9990001112",
                "episode_type": "F",
            },
            {"status": "failed"},
            {"status": "failed", "description": "Patient has an exit code"},
        )

        results = Helper.fetchall("failures", [the_date.date(), "BSO1"])

        assert len(results) == 1
        assert list(results[0])[0] == 9990001111

    @time_machine.travel("2025-03-30 10:00:00", tick=False)
    @pytest.mark.django_db
    def test_appointments_around_bst_start(self):
        """
        Test appointments near the BST start boundary (March 30, 2025).
        """

        # Before bst (should be excluded)
        before_bst = datetime(
            2025, 3, 30, 00, 30, tzinfo=ZONE_INFO
        )  # 30 mins before boundary
        # After bst (should be included)
        after_bst = datetime(
            2025, 3, 30, 1, 30, tzinfo=ZONE_INFO
        )  # 30 mins after boundary

        self.create_message_set(
            {
                "starts_at": before_bst,
                "nhs_number": "9990001111",
                "episode_type": "S",
            },
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )

        self.create_message_set(
            {
                "starts_at": after_bst,
                "nhs_number": "9990001111",
                "episode_type": "S",
            },
            {"status": "failed"},
            {"status": "failed", "description": "No reachable communication channel"},
        )

        results = Helper.fetchall(
            "failures", [datetime.now(tz=ZONE_INFO).date(), "BSO1"]
        )

        assert len(results) == 2

    @pytest.mark.django_db
    def test_failures_query_columns(self):
        with connection.cursor() as cursor:
            cursor.execute(
                Helper.sql("failures") + "\nLIMIT 0",
                [datetime.now(tz=ZONE_INFO).date(), "BSO1"],
            )
            columns = [col[0] for col in cursor.description]

        assert columns == [
            "NHS number",
            "Appointment date",
            "Clinic code",
            "Episode type",
            "Failed date",
            "Reason",
        ]
