import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment():
    return AppointmentFactory.create()


@pytest.mark.django_db
class TestStartScreening:
    def test_appointment_continued(self, client, appointment):
        response = client.post(
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
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
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
            {"decision": "dropout"},
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_cannot_go_ahead",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_renders_invalid_form(self, client, appointment):
        response = client.post(
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
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
            reverse("mammograms:show_appointment", kwargs={"pk": appointment.pk}),
        )
