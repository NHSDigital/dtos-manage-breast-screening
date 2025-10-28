import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestShowAppointment:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAskForMedicalInformation:
    def test_continue_to_record(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {"decision": "yes"},
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_continue_to_imaging(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {"decision": "no"},
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:awaiting_images",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_renders_invalid_form(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assertContains(response, "There is a problem")


@pytest.mark.django_db
class TestRecordMedicalInformation:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestCheckIn:
    def test_known_redirect(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse("mammograms:check_in", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
        )

    def test_audit(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse("mammograms:check_in", kwargs={"pk": appointment.pk})
        )
        assert (
            AuditLog.objects.filter(
                content_type=ContentType.objects.get_for_model(AppointmentStatus),
                operation=AuditLog.Operations.CREATE,
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestStartAppointment:
    def test_known_redirect(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse("mammograms:start_appointment", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:ask_for_medical_information", kwargs={"pk": appointment.pk}
            ),
        )

    def test_audit(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse("mammograms:start_appointment", kwargs={"pk": appointment.pk})
        )
        assert (
            AuditLog.objects.filter(
                content_type=ContentType.objects.get_for_model(AppointmentStatus),
                operation=AuditLog.Operations.CREATE,
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestAppointmentCannotGoAhead:
    def test_audit(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_cannot_go_ahead", kwargs={"pk": appointment.pk}
            ),
            {
                "stopped_reasons": ["failed_identity_check"],
                "decision": "True",
            },
        )
        assert (
            AuditLog.objects.filter(
                object_id=appointment.pk,
                operation=AuditLog.Operations.UPDATE,
            ).count()
            == 1
        )
