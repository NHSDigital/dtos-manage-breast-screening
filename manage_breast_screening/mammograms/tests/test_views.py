import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment():
    return AppointmentFactory.create()


@pytest.fixture
def completed_appointment():
    return AppointmentFactory.create(current_status=AppointmentStatus.SCREENED)


@pytest.mark.django_db
class TestShowAppointment:
    def test_redirects_if_in_progress(self, client, appointment):
        response = client.get(
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:start_screening",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_renders_response(self, client, completed_appointment):
        response = client.get(
            reverse(
                "mammograms:show_appointment", kwargs={"pk": completed_appointment.pk}
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestStartScreening:
    def test_appointment_continued(self, client, appointment):
        response = client.post(
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

    def test_appointment_stopped(self, client, appointment):
        response = client.post(
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
        self, client, completed_appointment
    ):
        response = client.get(
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

    def test_renders_invalid_form(self, client, appointment):
        response = client.post(
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
            {},
        )
        assertContains(response, "There is a problem")


@pytest.mark.django_db
class TestAskForMedicalInformation:
    def test_continue_to_record(self, client, appointment):
        response = client.post(
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

    def test_continue_to_imaging(self, client, appointment):
        response = client.post(
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

    def test_renders_invalid_form(self, client, appointment):
        response = client.post(
            reverse(
                "mammograms:ask_for_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assertContains(response, "There is a problem")


@pytest.mark.django_db
class TestCheckIn:
    def test_known_redirect(self, client, appointment):
        response = client.post(
            reverse("mammograms:check_in", kwargs={"pk": appointment.pk})
        )
        assertRedirects(
            response,
            reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
        )
