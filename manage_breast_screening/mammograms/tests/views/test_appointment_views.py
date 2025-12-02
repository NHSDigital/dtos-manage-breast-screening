import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models import AppointmentNote
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
class TestAppointmentNoteView:
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
