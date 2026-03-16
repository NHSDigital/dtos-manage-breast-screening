import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.core.tests.factories import UserFactory
from manage_breast_screening.manual_images.tests.factories import StudyFactory
from manage_breast_screening.participants.models import AppointmentNote
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestAppointmentNoteView:
    def test_delete_link_not_shown_when_note_does_not_exist(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Delete appointment note" not in response.content.decode()

    def test_delete_link_shown_when_note_exists(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        AppointmentNote.objects.create(appointment=appointment, content="Existing note")
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Delete appointment note" in response.content.decode()

    @pytest.mark.parametrize(
        "client_fixture", ["clinical_user_client", "administrative_user_client"]
    )
    def test_users_can_save_note(self, request, client_fixture):
        client = request.getfixturevalue(client_fixture)
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=client.current_provider
        )

        note_content = "Participant prefers left arm blood pressure readings."
        response = client.http.post(
            reverse(
                "mammograms:appointment_note",
                kwargs={"pk": appointment.pk},
            ),
            {"content": note_content},
        )

        assertRedirects(
            response,
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk}),
        )
        saved_note = AppointmentNote.objects.get(appointment=appointment)
        assert saved_note.content == note_content

    def test_save_redirects_to_return_url(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        check_info_url = reverse(
            "mammograms:check_information", kwargs={"pk": appointment.pk}
        )
        response = clinical_user_client.http.post(
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk})
            + f"?return_url={check_info_url}",
            {"content": "Test note content"},
        )
        assertRedirects(response, check_info_url, fetch_redirect_response=False)

    @pytest.mark.parametrize(
        "client_fixture", ["clinical_user_client", "administrative_user_client"]
    )
    def test_users_can_update_note(self, request, client_fixture):
        client = request.getfixturevalue(client_fixture)
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=client.current_provider
        )
        note = AppointmentNote.objects.create(
            appointment=appointment, content="Original note"
        )

        updated_content = "Updated note content"
        response = client.http.post(
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk}),
            {"content": updated_content},
        )

        assertRedirects(
            response,
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk}),
        )
        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == updated_content
        assert AppointmentNote.objects.count() == 1


@pytest.mark.django_db
class TestAppointmentNoteReviewView:
    def test_delete_link_not_shown_when_note_does_not_exist(
        self, clinical_user_client, clinical_user
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user,
            },
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note_review",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Appointment note" in response.content.decode()
        assert "app-status-bar" in response.content.decode()
        assert "Delete appointment note" not in response.content.decode()

    def test_delete_link_shown_when_note_exists(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status=AppointmentStatusNames.SCHEDULED,
        )
        AppointmentNote.objects.create(appointment=appointment, content="Existing note")
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_note_review",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "Delete appointment note" in response.content.decode()

    def test_users_can_save_note(self, clinical_user_client, clinical_user):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user,
            },
        )
        StudyFactory.create(appointment=appointment)

        note_content = "Participant prefers left arm blood pressure readings."
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_note_review",
                kwargs={"pk": appointment.pk},
            ),
            {"content": note_content},
        )

        assertRedirects(
            response,
            reverse("mammograms:check_information", kwargs={"pk": appointment.pk}),
        )
        saved_note = AppointmentNote.objects.get(appointment=appointment)
        assert saved_note.content == note_content

    def test_save_redirects_to_return_url(self, clinical_user_client, clinical_user):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user,
            },
        )
        check_info_url = reverse(
            "mammograms:check_information", kwargs={"pk": appointment.pk}
        )
        response = clinical_user_client.http.post(
            reverse("mammograms:appointment_note_review", kwargs={"pk": appointment.pk})
            + f"?return_url={check_info_url}",
            {"content": "Test note content"},
        )
        assertRedirects(response, check_info_url, fetch_redirect_response=False)

    def test_users_can_update_note(self, clinical_user_client, clinical_user):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user,
            },
        )
        StudyFactory.create(appointment=appointment)
        note = AppointmentNote.objects.create(
            appointment=appointment, content="Original note"
        )

        updated_content = "Updated note content"
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_note_review", kwargs={"pk": appointment.pk}
            ),
            {"content": updated_content},
        )

        assertRedirects(
            response,
            reverse("mammograms:check_information", kwargs={"pk": appointment.pk}),
        )
        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == updated_content
        assert AppointmentNote.objects.count() == 1

    def test_access_denied_for_administrative_users(
        self, administrative_user_client, clinical_user
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=administrative_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": clinical_user,
            },
        )
        note = AppointmentNote.objects.create(
            appointment=appointment, content="Original note"
        )

        response = administrative_user_client.http.post(
            reverse(
                "mammograms:appointment_note_review", kwargs={"pk": appointment.pk}
            ),
            {"content": "Updated note content"},
        )

        assert response.status_code == 403
        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == "Original note"
        assert AppointmentNote.objects.count() == 1

    def test_access_denied_when_not_in_progress(
        self, clinical_user_client, clinical_user
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.SCREENED,
                "created_by": UserFactory.create(),
            },
        )
        note = AppointmentNote.objects.create(
            appointment=appointment, content="Original note"
        )
        StudyFactory.create(appointment=appointment)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_note_review", kwargs={"pk": appointment.pk}
            ),
            {"content": "Updated note content"},
        )
        assertRedirects(
            response,
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
        )

        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == "Original note"
        assert AppointmentNote.objects.count() == 1

    def test_access_denied_when_in_progress_with_another_user(
        self, clinical_user_client, clinical_user
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": UserFactory.create(),
            },
        )
        note = AppointmentNote.objects.create(
            appointment=appointment, content="Original note"
        )
        StudyFactory.create(appointment=appointment)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:appointment_note_review", kwargs={"pk": appointment.pk}
            ),
            {"content": "Updated note content"},
        )
        assertRedirects(
            response,
            reverse("mammograms:check_information", kwargs={"pk": appointment.pk}),
        )

        updated_note = AppointmentNote.objects.get(pk=note.pk)
        assert updated_note.content == "Updated note content"
        assert AppointmentNote.objects.count() == 1


@pytest.mark.django_db
class TestDeleteAppointmentNoteView:
    def test_get_redirects_when_note_does_not_exist(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk}),
        )

    def test_post_redirects_when_note_does_not_exist(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse("mammograms:appointment_note", kwargs={"pk": appointment.pk}),
        )

    def test_post_redirects_to_return_url(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

        check_info_url = reverse(
            "mammograms:check_information", kwargs={"pk": appointment.pk}
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": appointment.pk},
            )
            + f"?return_url={check_info_url}"
        )
        assertRedirects(response, check_info_url, fetch_redirect_response=False)
