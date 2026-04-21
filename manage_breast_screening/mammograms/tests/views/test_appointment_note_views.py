import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
class TestDeleteAppointmentNoteView:
    def test_get_redirects_when_note_does_not_exist(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            ),
        )

    def test_post_redirects_when_note_does_not_exist(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_note", kwargs={"pk": in_progress_appointment.pk}
            ),
        )

    def test_post_redirects_to_return_url(
        self, clinical_user_client, in_progress_appointment
    ):
        check_info_url = reverse(
            "mammograms:check_information", kwargs={"pk": in_progress_appointment.pk}
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_appointment_note",
                kwargs={"pk": in_progress_appointment.pk},
            )
            + f"?return_url={check_info_url}"
        )
        assertRedirects(response, check_info_url, fetch_redirect_response=False)
