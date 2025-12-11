import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.participants.models import AppointmentNote
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
