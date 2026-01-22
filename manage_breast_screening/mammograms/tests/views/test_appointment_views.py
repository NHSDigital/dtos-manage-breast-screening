import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertQuerySetEqual, assertRedirects

from manage_breast_screening.config.settings import LOGIN_URL
from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models import MedicalInformationReview
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    MedicalInformationReviewFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory


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
class TestConfirmIdentity:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:confirm_identity",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_redirects_to_medical_information_page(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:confirm_identity",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_records_completion(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse(
                "mammograms:confirm_identity",
                kwargs={"pk": appointment.pk},
            )
        )

        assertQuerySetEqual(
            appointment.completed_workflow_steps.filter(
                created_by=clinical_user_client.user
            )
            .values_list("step_name", flat=True)
            .distinct(),
            [AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY],
        )


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

    def test_records_completion(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        clinical_user_client.http.post(
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assertQuerySetEqual(
            appointment.completed_workflow_steps.filter(
                created_by=clinical_user_client.user
            )
            .values_list("step_name", flat=True)
            .distinct(),
            [AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION],
        )


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
            reverse("mammograms:confirm_identity", kwargs={"pk": appointment.pk}),
        )

    def test_user_not_permitted(self, administrative_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=administrative_user_client.current_provider
        )
        url = reverse("mammograms:start_appointment", kwargs={"pk": appointment.pk})
        response = administrative_user_client.http.post(url)
        assertRedirects(response, reverse(LOGIN_URL, query={"next": url}))


@pytest.mark.django_db
class TestAppointmentCannotGoAhead:
    def test_status_and_audit_created(self, clinical_user_client):
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


@pytest.mark.django_db
class TestMarkSectionReviewed:
    def test_creates_medical_information_review(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:mark_section_reviewed",
                kwargs={"pk": appointment.pk, "section": "SYMPTOMS"},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assert MedicalInformationReview.objects.filter(
            appointment=appointment, section="SYMPTOMS"
        ).exists()
        review = MedicalInformationReview.objects.get(
            appointment=appointment, section="SYMPTOMS"
        )
        assert review.reviewed_by == clinical_user_client.user

    def test_does_not_update_reviewed_by_if_already_reviewed(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        original_user = UserFactory.create(first_name="Jane", last_name="Doe")
        MedicalInformationReviewFactory.create(
            appointment=appointment, section="SYMPTOMS", reviewed_by=original_user
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:mark_section_reviewed",
                kwargs={"pk": appointment.pk, "section": "SYMPTOMS"},
            ),
            follow=True,
        )

        review = MedicalInformationReview.objects.get(
            appointment=appointment, section="SYMPTOMS"
        )
        assert review.reviewed_by == original_user
        assertContains(
            response,
            "This section has already been reviewed by Jane Doe",
        )
