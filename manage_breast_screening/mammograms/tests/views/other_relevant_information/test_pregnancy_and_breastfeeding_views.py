import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.other_information.pregnancy_and_breastfeeding import (
    PregnancyAndBreastfeeding,
)
from manage_breast_screening.participants.tests.factories import (
    PregnancyAndBreastfeedingFactory,
)


@pytest.mark.django_db
class TestAddPregnancyAndBreastfeedingView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_pregnancy_and_breastfeeding",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_redirects_if_already_exists(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        PregnancyAndBreastfeedingFactory.create(
            appointment=confirmed_identity_appointment
        )

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_pregnancy_and_breastfeeding",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_pregnancy_and_breastfeeding",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
                "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added pregnancy and breastfeeding",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_pregnancy_and_breastfeeding",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_pregnancy_status">Select whether they are currently pregnant or not</a></li>
                    <li><a href="#id_breastfeeding_status">Select whether they are currently breastfeeding or not</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangePregnancyAndBreastfeedingView:
    @pytest.fixture
    def pregnancy_and_breastfeeding(self, confirmed_identity_appointment):
        return PregnancyAndBreastfeedingFactory.create(
            appointment=confirmed_identity_appointment
        )

    def test_renders_response(self, clinical_user_client, pregnancy_and_breastfeeding):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_pregnancy_and_breastfeeding",
                kwargs={
                    "pk": pregnancy_and_breastfeeding.appointment.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, pregnancy_and_breastfeeding
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_pregnancy_and_breastfeeding",
                kwargs={"pk": pregnancy_and_breastfeeding.appointment.pk},
            ),
            {
                "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
                "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": pregnancy_and_breastfeeding.appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated pregnancy and breastfeeding",
                )
            ],
        )
