from unittest.mock import patch

import django
import pytest
import statemachine
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertInHTML,
    assertQuerySetEqual,
    assertRedirects,
)

from manage_breast_screening.config.settings import LOGIN_URL
from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.gateway.models import GatewayAction, GatewayActionType
from manage_breast_screening.gateway.tests.factories import RelayFactory
from manage_breast_screening.mammograms.forms.images.record_images_taken_form import (
    RecordImagesTakenForm,
)
from manage_breast_screening.manual_images.models import Study
from manage_breast_screening.participants.models import MedicalInformationReview
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    MedicalInformationReviewFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestConfirmIdentity:
    def test_renders_response_when_identity_not_confirmed(self, clinical_user_client):
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
        assertInHTML(
            """
            <button class="nhsuk-button nhsuk-u-margin-bottom-0" data-module="nhsuk-button" type="submit">
                Confirm identity
            </button>
            """,
            response.text,
        )

    def test_renders_response_when_identity_confirmed_by_a_different_user(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        # Create CONFIRM_IDENTITY step for a different user before the POST, to confirm correct button text
        appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:confirm_identity",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <button class="nhsuk-button nhsuk-u-margin-bottom-0" data-module="nhsuk-button" type="submit">
                Confirm identity
            </button>
            """,
            response.text,
        )

    def test_renders_response_when_identity_confirmed_by_same_user(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        # Create CONFIRM_IDENTITY step for this user before the POST, to confirm correct button text
        appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=clinical_user_client.user,
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:confirm_identity",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <button class="nhsuk-button nhsuk-u-margin-bottom-0" data-module="nhsuk-button" type="submit">
                Next section
            </button>
            """,
            response.text,
        )

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
                "mammograms:record_medical_information",
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
            ).values_list("step_name", flat=True),
            [AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY],
        )

    def test_does_record_completion_even_when_already_confirmed_by_different_user(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        # Create CONFIRM_IDENTITY for a different user before the POST, to confirm a new record is created
        appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid="different_user"),
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
            ).values_list("step_name", flat=True),
            [AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY],
        )

    def test_does_not_record_completion_if_already_confirmed_by_this_user(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        # Create CONFIRM_IDENTITY for this user before the POST, to confirm no duplicate is created
        appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=clinical_user_client.user,
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
            ).values_list("step_name", flat=True),
            [AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY],
        )


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

    @patch("manage_breast_screening.gateway.relay_service.RelayService.send_action")
    def test_creates_gateway_action(self, mock_send_action, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        relay = RelayFactory.create(provider=appointment.provider)
        clinical_user_client.http.post(
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        action = GatewayAction.objects.get(appointment=appointment)
        assert action.type == GatewayActionType.WORKLIST_CREATE
        assert (
            action.payload["parameters"]["worklist_item"]["participant"]["nhs_number"]
            == appointment.participant.nhs_number
        )
        mock_send_action.assert_called_once_with(relay, action)


@pytest.mark.django_db
class TestTakeImages:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:take_images",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_no_images_redirects_to_cannot_continue(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:take_images",
                kwargs={"pk": appointment.pk},
            ),
            {
                "standard_images": RecordImagesTakenForm.StandardImagesChoices.NO_IMAGES_TAKEN
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_cannot_go_ahead", kwargs={"pk": appointment.pk}
            ),
        )

    @pytest.mark.xfail(reason="The additional details view is not implemented yet")
    def test_additional_info_redirects_to_additional_details(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:take_images",
                kwargs={"pk": appointment.pk},
            ),
            {
                "standard_images": RecordImagesTakenForm.StandardImagesChoices.NO_ADD_ADDITIONAL
            },
        )
        assertRedirects(
            response,
            reverse("mammograms:add_image_details", kwargs={"pk": appointment.pk}),
        )

    def test_yes_marks_the_step_complete_and_redirects_to_check_info(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:take_images",
                kwargs={"pk": appointment.pk},
            ),
            {
                "standard_images": RecordImagesTakenForm.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO
            },
        )
        assertRedirects(
            response,
            reverse("mammograms:check_information", kwargs={"pk": appointment.pk}),
        )
        assertQuerySetEqual(
            appointment.completed_workflow_steps.filter(
                created_by=clinical_user_client.user
            )
            .values_list("step_name", flat=True)
            .distinct(),
            [AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES],
        )

    def test_redirects_to_update_image_details_when_series_exist(
        self, clinical_user_client, appointment
    ):
        study = Study.objects.create(appointment=appointment)
        study.series_set.create(view_position="CC", laterality="R", count=1)

        response = clinical_user_client.http.get(
            reverse("mammograms:take_images", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse("mammograms:update_image_details", kwargs={"pk": appointment.pk}),
            target_status_code=302,
        )

    def test_yes_creates_the_study(self, clinical_user_client, appointment):
        clinical_user_client.http.post(
            reverse(
                "mammograms:take_images",
                kwargs={"pk": appointment.pk},
            ),
            {
                "standard_images": RecordImagesTakenForm.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO
            },
        )
        assertQuerySetEqual(
            appointment.study.series_set.values_list(
                "view_position", "laterality", "count"
            ),
            {("CC", "L", 1), ("CC", "R", 1), ("MLO", "L", 1), ("MLO", "R", 1)},
            ordered=False,
        )


@pytest.mark.django_db
class TestAppointmentImagesStream:
    def test_returns_sse_content_type(self, clinical_user_client, appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_images_stream", kwargs={"pk": appointment.pk}
            )
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"

    def test_returns_404_for_unknown_appointment(self, clinical_user_client):
        import uuid

        response = clinical_user_client.http.get(
            reverse("mammograms:appointment_images_stream", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404


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
class TestResumeAppointment:
    @pytest.fixture
    def paused_appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status=AppointmentStatusNames.PAUSED,
        )

    def test_can_resume_when_in_progress_with_user(self, clinical_user_client):
        """
        A user should still be able to resume an in progress appointment when it's in progress with them.
        """
        in_progress_appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user_client.user,
            },
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:confirm_identity", kwargs={"pk": in_progress_appointment.pk}
            ),
        )

    def test_cannot_resume_when_in_progress_with_different_user(
        self, clinical_user_client
    ):
        """
        A user should not be able to resume an in progress appointment when it's in progress with a different user.
        """
        different_user = UserFactory.create(nhs_uid="different_user")
        in_progress_appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": different_user,
            },
        )

        with pytest.raises(
            statemachine.exceptions.TransitionNotAllowed,
            match="Can't Resume when in In progress.",
        ):
            clinical_user_client.http.post(
                reverse(
                    "mammograms:resume_appointment",
                    kwargs={"pk": in_progress_appointment.pk},
                )
            )

        in_progress_appointment.refresh_from_db()
        assert (
            in_progress_appointment.current_status.name
            == AppointmentStatusNames.IN_PROGRESS
        )
        assert in_progress_appointment.current_status.created_by == different_user

    def test_redirect_confirm_identity(self, clinical_user_client, paused_appointment):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:confirm_identity", kwargs={"pk": paused_appointment.pk}
            ),
        )
        paused_appointment.refresh_from_db()
        assert (
            paused_appointment.current_status.name == AppointmentStatusNames.IN_PROGRESS
        )
        assert paused_appointment.current_status.created_by == clinical_user_client.user

    def test_redirect_confirm_identity_when_already_confirmed(
        self, clinical_user_client, paused_appointment
    ):
        """
        If identity confirmation was completed by a different user,
        the current user should still be required to confirm identity and not be redirected to the next step.
        """
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:confirm_identity", kwargs={"pk": paused_appointment.pk}
            ),
        )

    def test_redirect_check_information_when_already_taken_images(
        self, clinical_user_client, paused_appointment
    ):
        """
        If identity confirmation was completed by a different user,
        the current user should still be required to confirm identity even if images have already been taken.
        """
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        # check_information expects appointment to have a Study
        Study.objects.create(appointment=paused_appointment)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:confirm_identity", kwargs={"pk": paused_appointment.pk}
            ),
        )

    def test_redirect_record_medical_information(
        self, clinical_user_client, paused_appointment
    ):
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": paused_appointment.pk},
            ),
        )

    def test_redirect_take_images(self, clinical_user_client, paused_appointment):
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse("mammograms:take_images", kwargs={"pk": paused_appointment.pk}),
        )

    def test_redirect_check_information(self, clinical_user_client, paused_appointment):
        """
        Redirect to check information when all previous steps have been completed by the user.
        """
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )
        # check_information expects appointment to have a Study
        Study.objects.create(appointment=paused_appointment)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information", kwargs={"pk": paused_appointment.pk}
            ),
        )

    def test_redirect_check_information_when_images_taken_by_different_user(
        self, clinical_user_client, paused_appointment
    ):
        """
        If the user has already confirmed identity,
        redirect to check information when all previous steps have been completed - even if completed by a different user.
        """
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            created_by=UserFactory.create(nhs_uid="different_user"),
        )
        paused_appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=UserFactory.create(nhs_uid=clinical_user_client.user.nhs_uid),
        )
        # check_information expects appointment to have a Study
        Study.objects.create(appointment=paused_appointment)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information", kwargs={"pk": paused_appointment.pk}
            ),
        )

    def test_user_not_permitted(self, administrative_user_client, paused_appointment):
        url = reverse(
            "mammograms:resume_appointment", kwargs={"pk": paused_appointment.pk}
        )
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


@pytest.mark.django_db
class TestPauseAppointment:
    @pytest.fixture
    def in_progress_appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user_client.user,
            },
        )

    def test_renders_response(self, clinical_user_client, in_progress_appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:pause_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML(
            f"""
            <h1 class="nhsuk-heading-l">
                <span class="nhsuk-caption-l">
                    {in_progress_appointment.participant.full_name}
                </span>
                Pause this appointment
            </h1>
            """,
            response.text,
        )

    def test_can_pause_when_in_progress_with_user(
        self, clinical_user_client, in_progress_appointment
    ):
        """
        A user should be able to pause an in progress appointment when it's in progress with them.
        """
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:pause_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "clinics:show",
                kwargs={"pk": in_progress_appointment.clinic_slot.clinic.pk},
            ),
        )

        in_progress_appointment.refresh_from_db()
        assert (
            in_progress_appointment.current_status.name == AppointmentStatusNames.PAUSED
        )
        assert (
            in_progress_appointment.current_status.created_by
            == clinical_user_client.user
        )

    def test_cannot_pause_when_not_in_progress(self, clinical_user_client):
        """
        A user should not be able to pause an in progress appointment when it's not in progress.
        """
        screened_appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.SCREENED,
                "created_by": clinical_user_client.user,
            },
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:pause_appointment",
                kwargs={"pk": screened_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:show_appointment", kwargs={"pk": screened_appointment.pk}
            ),
        )

        screened_appointment.refresh_from_db()
        assert (
            screened_appointment.current_status.name == AppointmentStatusNames.SCREENED
        )
        assert (
            screened_appointment.current_status.created_by == clinical_user_client.user
        )

    def test_cannot_pause_when_in_progress_with_different_user(
        self, clinical_user_client
    ):
        """
        A user should not be able to pause an in progress appointment when it's in progress with a different user.
        """
        different_user = UserFactory.create(nhs_uid="different_user")
        in_progress_appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": different_user,
            },
        )

        with pytest.raises(
            django.core.exceptions.ValidationError,
            match="Can't pause when not in progress with the user",
        ):
            clinical_user_client.http.post(
                reverse(
                    "mammograms:pause_appointment",
                    kwargs={"pk": in_progress_appointment.pk},
                )
            )

        in_progress_appointment.refresh_from_db()
        assert (
            in_progress_appointment.current_status.name
            == AppointmentStatusNames.IN_PROGRESS
        )
        assert in_progress_appointment.current_status.created_by == different_user

    def test_user_not_permitted(
        self, administrative_user_client, in_progress_appointment
    ):
        url = reverse(
            "mammograms:pause_appointment", kwargs={"pk": in_progress_appointment.pk}
        )
        assert administrative_user_client.http.get(url).status_code == 403
        assert administrative_user_client.http.post(url).status_code == 403
