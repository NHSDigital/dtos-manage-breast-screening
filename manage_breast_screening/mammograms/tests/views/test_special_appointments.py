import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.mammograms.tests.forms.test_special_appointment_forms import (
    SupportReasons,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestProvideDetails:
    def test_get_renders_a_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [SupportReasons.MEDICAL_DEVICES],
                "medical_devices_details": "has pacemaker",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_valid_post_creates_an_audit_record(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [SupportReasons.LANGUAGE],
                "language_details": "learning english",
            },
        )
        assert (
            AuditLog.objects.filter(
                object_id=appointment.participant.pk,
                operation=AuditLog.Operations.UPDATE,
            ).count()
            == 1
        )

    def test_invalid_post_to_provide_details_page_renders_response(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
