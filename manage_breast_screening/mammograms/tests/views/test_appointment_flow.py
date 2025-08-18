import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models import AppointmentStatus


@pytest.mark.django_db
class TestShowAppointment:
    def test_viewable_by_clinical_or_administrative(
        self, clinical_user_client, administrative_user_client, completed_appointment
    ):
        response = clinical_user_client.get(
            reverse(
                "mammograms:show_appointment", kwargs={"pk": completed_appointment.pk}
            )
        )
        assert response.status_code == 200

        response = administrative_user_client.get(
            reverse(
                "mammograms:show_appointment", kwargs={"pk": completed_appointment.pk}
            )
        )
        assert response.status_code == 200

    def test_redirects_to_show_screening_if_in_progress(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.get(
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:start_screening",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_doesnt_redirect_if_not_permitted(
        self, administrative_user_client, appointment
    ):
        response = administrative_user_client.get(
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk})
        )
        assert response.status_code == 200

    def test_renders_response(self, clinical_user_client, completed_appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:show_appointment", kwargs={"pk": completed_appointment.pk}
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestStartScreening:
    def test_viewable_by_clinical_only(
        self, clinical_user_client, administrative_user_client, client, appointment
    ):
        response = clinical_user_client.get(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk})
        )
        assert response.status_code == 200

        response = administrative_user_client.get(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk})
        )
        assert response.status_code == 403

    def test_appointment_continued(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
            {"decision": "continue"},
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_appointment_stopped(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
            {"decision": "dropout"},
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_cannot_go_ahead",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_already_completed_appointment_redirects(
        self, clinical_user_client, completed_appointment
    ):
        response = clinical_user_client.get(
            reverse(
                "mammograms:start_screening", kwargs={"pk": completed_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": completed_appointment.pk},
            ),
        )

    def test_renders_invalid_form(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
            {},
        )
        assertContains(response, "There is a problem")


@pytest.mark.django_db
class TestAskForMedicalInformation:
    def test_continue_to_record(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
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

    def test_continue_to_imaging(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
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

    def test_renders_invalid_form(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assertContains(response, "There is a problem")


@pytest.mark.django_db
class TestCheckIn:
    def test_known_redirect(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse("mammograms:check_in", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
        )

    def test_audit(self, clinical_user_client, appointment):
        clinical_user_client.post(
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
class TestAppointmentCannotGoAhead:
    def test_audit(self, clinical_user_client, appointment):
        clinical_user_client.post(
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
