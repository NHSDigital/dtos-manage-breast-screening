import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.mammograms.tests.forms.test_special_appointment_forms import (
    SupportReasons,
    TemporaryChoices,
)


@pytest.mark.django_db
class TestProvideDetails:
    def test_get_renders_a_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment_if_no_temporary_reasons(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [SupportReasons.MEDICAL_DEVICES],
                "medical_devices_details": "has pacemaker",
                "any_temporary": TemporaryChoices.NO,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:start_screening",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_valid_post_redirects_to_appointment_if_one_temporary_reason(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [SupportReasons.LANGUAGE],
                "language_details": "learning english",
                "any_temporary": TemporaryChoices.YES,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:start_screening",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_valid_post_creates_an_audit_record(
        self, clinical_user_client, appointment
    ):
        clinical_user_client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [SupportReasons.LANGUAGE],
                "language_details": "learning english",
                "any_temporary": TemporaryChoices.YES,
            },
        )
        assert (
            AuditLog.objects.filter(
                object_id=appointment.participant.pk,
                operation=AuditLog.Operations.UPDATE,
            ).count()
            == 1
        )

    def test_valid_post_redirects_to_next_step_if_some_temporary_reasons(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "support_reasons": [
                    SupportReasons.PHYSICAL_RESTRICTION,
                    SupportReasons.VISION,
                ],
                "physical_restriction_details": "broken leg",
                "vision_details": "blind",
                "any_temporary": TemporaryChoices.YES,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:mark_reasons_temporary",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_invalid_post_to_provide_details_page_renders_response(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestMarkTemporary:
    def test_get_renders_a_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:mark_reasons_temporary",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    @pytest.fixture
    def appointment_with_selected_reasons(self, appointment):
        """
        Emulate the state of the appointment after the first form has been completed
        """
        participant = appointment.participant
        participant.extra_needs = {
            SupportReasons.MEDICAL_DEVICES: {"details": "abc"},
            SupportReasons.HEARING: {"details": "abc"},
        }
        participant.save()
        return appointment

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment_with_selected_reasons
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:mark_reasons_temporary",
                kwargs={"pk": appointment_with_selected_reasons.pk},
            ),
            {
                "which_are_temporary": [SupportReasons.MEDICAL_DEVICES],
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:start_screening",
                kwargs={"pk": appointment_with_selected_reasons.pk},
            ),
        )

    def test_valid_post_creates_an_audit_record(
        self, clinical_user_client, appointment_with_selected_reasons
    ):
        clinical_user_client.post(
            reverse(
                "mammograms:mark_reasons_temporary",
                kwargs={"pk": appointment_with_selected_reasons.pk},
            ),
            {
                "which_are_temporary": [SupportReasons.MEDICAL_DEVICES],
            },
        )

        assert (
            AuditLog.objects.filter(
                object_id=appointment_with_selected_reasons.participant.pk,
                operation=AuditLog.Operations.UPDATE,
            ).count()
            == 1
        )

    def test_invalid_post_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.post(
            reverse(
                "mammograms:mark_reasons_temporary",
                kwargs={"pk": appointment.pk},
            ),
            {"which_are_temporary": []},
        )
        assert response.status_code == 200
