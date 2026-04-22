from unittest.mock import patch

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertInHTML, assertRedirects

from manage_breast_screening.dicom.tests.factories import (
    ImageFactory as DicomImageFactory,
)
from manage_breast_screening.dicom.tests.factories import (
    StudyFactory as DicomStudyFactory,
)
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.participants.models import AppointmentNote
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestShowAppointmentView:
    def test_renders_response(self, clinical_user_client, in_progress_appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestShowMedicalInformationView:
    def test_displays_medical_information_sections(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assertContains(response, "Mammogram history")
        assertContains(response, "Symptoms")
        assertContains(response, "Medical history")
        assertContains(response, "Breast features")
        assertContains(response, "Other information")


@pytest.mark.django_db
class TestImages:
    def test_renders_view_counts(self, clinical_user_client, completed_appointment):
        study = StudyFactory(appointment=completed_appointment)
        SeriesFactory(study=study, view_position="MLO", laterality="R", count=1)
        SeriesFactory(study=study, view_position="CC", laterality="R", count=1)
        SeriesFactory(study=study, view_position="MLO", laterality="L", count=1)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_image_details",
                kwargs={"pk": completed_appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML("1× RMLO", response.text)
        assertInHTML("1× RCC", response.text)
        assertInHTML("1× LMLO", response.text)
        assertInHTML("0× LCC", response.text)

    @patch(
        "manage_breast_screening.mammograms.presenters.appointment_presenters.gateway_images_enabled",
        return_value=True,
    )
    def test_renders_gateway_images_view_counts(
        self, _, clinical_user_client, completed_appointment
    ):
        action = GatewayActionFactory(appointment=completed_appointment)
        study = DicomStudyFactory(source_message_id=action.id)
        DicomImageFactory(series__study=study, view_position="MLO", laterality="R")
        DicomImageFactory(series__study=study, view_position="CC", laterality="R")
        DicomImageFactory(series__study=study, view_position="MLO", laterality="L")

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_image_details",
                kwargs={"pk": completed_appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML("1× RMLO", response.text)
        assertInHTML("1× RCC", response.text)
        assertInHTML("1× LMLO", response.text)
        assertInHTML("0× LCC", response.text)


@pytest.mark.django_db
class TestUpsertAppointmentNoteView:
    def test_delete_link_not_shown_when_note_does_not_exist(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Delete appointment note" not in response.content.decode()

    def test_delete_link_shown_when_note_exists(
        self, clinical_user_client, in_progress_appointment
    ):
        AppointmentNote.objects.create(
            appointment=in_progress_appointment, content="Existing note"
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Delete appointment note" in response.content.decode()

    @pytest.mark.parametrize(
        "client_fixture", ["clinical_user_client", "administrative_user_client"]
    )
    def test_users_can_save_note(
        self, request, client_fixture, in_progress_appointment
    ):
        client = request.getfixturevalue(client_fixture)

        note_content = "Participant prefers left arm blood pressure readings."
        response = client.http.post(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            ),
            {"content": note_content},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            ),
        )
        saved_note = AppointmentNote.objects.get(appointment=in_progress_appointment)
        assert saved_note.content == note_content

    def test_save_redirects_to_return_url(
        self, clinical_user_client, in_progress_appointment
    ):
        check_info_url = reverse(
            "mammograms:check_information", kwargs={"pk": in_progress_appointment.pk}
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            )
            + f"?return_url={check_info_url}",
            {"content": "Test note content"},
        )
        assertRedirects(response, check_info_url, fetch_redirect_response=False)

    @pytest.mark.parametrize(
        "client_fixture", ["clinical_user_client", "administrative_user_client"]
    )
    def test_users_can_update_note(
        self, request, client_fixture, in_progress_appointment
    ):
        client = request.getfixturevalue(client_fixture)
        note = AppointmentNote.objects.create(
            appointment=in_progress_appointment, content="Original note"
        )

        updated_content = "Updated note content"
        response = client.http.post(
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            ),
            {"content": updated_content},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            ),
        )
        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == updated_content
        assert AppointmentNote.objects.count() == 1
