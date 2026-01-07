from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models import AppointmentReportedMammogram
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentReportedMammogramFactory,
)

from ...forms import AppointmentProceedAnywayForm


@pytest.mark.django_db
class TestAppointmentProceedAnywayForm:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def appointment_reported_mammogram(self, appointment):
        return AppointmentReportedMammogramFactory.create(
            appointment=appointment,
            location_type=AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        )

    def test_missing_reason_for_continuing(
        self, appointment, appointment_reported_mammogram
    ):
        form_data = {}
        form = AppointmentProceedAnywayForm(
            form_data,
            instance=appointment_reported_mammogram,
            participant=appointment.participant,
        )
        assert not form.is_valid()
        assert form.errors == {
            "reason_for_continuing": ["Provide a reason for continuing"]
        }
        appointment_reported_mammogram.refresh_from_db()
        assert not appointment_reported_mammogram.reason_for_continuing

    def test_update_mammogram_with_reason_for_continuing(
        self, appointment, appointment_reported_mammogram
    ):
        form_data = QueryDict(
            urlencode(
                {
                    "reason_for_continuing": ["a reason"],
                },
                doseq=True,
            )
        )
        form = AppointmentProceedAnywayForm(
            form_data,
            instance=appointment_reported_mammogram,
            participant=appointment.participant,
        )
        assert form.is_valid()
        form.update()
        appointment_reported_mammogram.refresh_from_db()
        assert appointment_reported_mammogram.reason_for_continuing == "a reason"
