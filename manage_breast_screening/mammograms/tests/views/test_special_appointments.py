import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.mammograms.tests.forms.test_special_appointment_forms import (
    SupportReasons,
    TemporaryChoices,
)


@pytest.mark.django_db
class TestSpecialAppointments:
    def test_get_renders_a_response(self, client, appointment):
        response = client.get(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(self, client, appointment):
        response = client.post(
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

    def test_invalid_post_renders_response(self, client, appointment):
        response = client.post(
            reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
