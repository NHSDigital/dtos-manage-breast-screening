from datetime import datetime, timedelta

import pytest

from manage_breast_screening.notifications.models import ZONE_INFO
from manage_breast_screening.notifications.queries.helper import Helper
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ClinicFactory,
)


@pytest.mark.django_db
class TestReconciliationQuery:
    def test_appointments_for_today_by_episode_type(self):
        clinic1 = ClinicFactory(bso_code="MDB", code="BU001")
        clinic2 = ClinicFactory(bso_code="MDB", code="BU002")
        clinic3 = ClinicFactory(bso_code="MDB", code="BU003")

        AppointmentFactory.create_batch(size=7, clinic=clinic1)
        AppointmentFactory.create_batch(size=8, clinic=clinic1, episode_type="R")
        AppointmentFactory.create_batch(size=2, clinic=clinic1, episode_type="G")
        AppointmentFactory.create_batch(
            size=2, clinic=clinic1, episode_type="G", status="C"
        )
        AppointmentFactory.create_batch(size=3, clinic=clinic1, episode_type="F")
        AppointmentFactory.create_batch(size=5, clinic=clinic1, episode_type="H")
        AppointmentFactory.create_batch(size=2, clinic=clinic2, episode_type="F")
        AppointmentFactory.create_batch(
            size=3, clinic=clinic2, episode_type="F", status="A"
        )
        AppointmentFactory.create_batch(size=9, clinic=clinic2, episode_type="H")
        AppointmentFactory.create_batch(size=5, clinic=clinic2, episode_type="N")
        AppointmentFactory.create_batch(size=2, clinic=clinic3)
        AppointmentFactory.create_batch(size=5, clinic=clinic3, episode_type="F")
        AppointmentFactory.create_batch(size=4, clinic=clinic3, episode_type="G")
        AppointmentFactory.create_batch(size=6, clinic=clinic3, episode_type="R")

        tomorrow_appt = AppointmentFactory(clinic=clinic1)
        tomorrow_appt.created_at = datetime.now(tz=ZONE_INFO) + timedelta(days=1)
        tomorrow_appt.save()

        results = Helper.fetchall(
            "reconciliation",
            (
                datetime.now(tz=ZONE_INFO).date(),
                "MDB",
            ),
        )

        assert len(results) == 14

        assert results[0] == ("BU001", "F", "B", 3)
        assert results[1] == ("BU001", "G", "B", 2)
        assert results[2] == ("BU001", "G", "C", 2)
        assert results[3] == ("BU001", "H", "B", 5)
        assert results[4] == ("BU001", "R", "B", 8)
        assert results[5] == ("BU001", "S", "B", 7)

        assert results[6] == ("BU002", "F", "A", 3)
        assert results[7] == ("BU002", "F", "B", 2)
        assert results[8] == ("BU002", "H", "B", 9)
        assert results[9] == ("BU002", "N", "B", 5)

        assert results[10] == ("BU003", "F", "B", 5)
        assert results[11] == ("BU003", "G", "B", 4)
        assert results[12] == ("BU003", "R", "B", 6)
        assert results[13] == ("BU003", "S", "B", 2)

    def test_appointments_filtered_for_specified_bso(self):
        clinic1 = ClinicFactory(bso_code="MDB", code="BU001")
        clinic2 = ClinicFactory(bso_code="WAT", code="BU002")
        AppointmentFactory.create_batch(size=2, clinic=clinic1)
        AppointmentFactory.create_batch(size=2, clinic=clinic2)

        results = Helper.fetchall(
            "reconciliation",
            (
                datetime.now(tz=ZONE_INFO).date(),
                "MDB",
            ),
        )
        assert len(results) == 1
        assert results[0] == ("BU001", "S", "B", 2)
