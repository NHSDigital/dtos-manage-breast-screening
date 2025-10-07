from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import connection

from manage_breast_screening.notifications.queries.failures_query import FailuresQuery
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
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
        appt = AppointmentFactory(**appt_params)
        message_params["sent_at"] = datetime.now() - timedelta(minutes=5)
        message = MessageFactory(appointment=appt, **message_params)
        if message_status_params:
            message_status_params["status_updated_at"] = datetime.now() - timedelta(
                minutes=7
            )
            MessageStatusFactory(message=message, **message_status_params)

        return appt

    @pytest.mark.django_db
    def test_failures_query_data_today(self):
        appt_time = datetime.now(tz=ZoneInfo("Europe/London"))
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
        today_formatted = datetime.today().strftime("%Y-%m-%d")

        with connection.cursor() as cursor:
            cursor.execute(FailuresQuery.sql(), (datetime.now().date(),))
            results = cursor.fetchall()

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
        ]

        for idx, res in enumerate(results):
            assert expectations[idx] == list(res)

    @pytest.mark.django_db
    def test_failures_query_for_given_date(self):
        the_date = datetime.today() - timedelta(days=2)
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

        with connection.cursor() as cursor:
            cursor.execute(FailuresQuery.sql(), (the_date.date(),))
            results = cursor.fetchall()

        assert len(results) == 1
        assert list(results[0])[0] == 9990001111

    def test_failures_query_columns(self):
        assert FailuresQuery.columns() == [
            "NHS number",
            "Appointment date",
            "Clinic code",
            "Episode type",
            "Failure date",
            "Failure reason",
        ]
