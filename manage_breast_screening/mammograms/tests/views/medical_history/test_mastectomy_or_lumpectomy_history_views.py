import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    MastectomyOrLumpectomyHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddMastectomyOrLumpectomyHistoryView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_mastectomy_or_lumpectomy_history_item",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_mastectomy_or_lumpectomy_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "right_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "left_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "surgery_reason": [
                    MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION
                ],
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added mastectomy or lumpectomy",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_mastectomy_or_lumpectomy_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_right_breast_procedure">Select which procedure they have had in the right breast</a></li>
                    <li><a href="#id_left_breast_procedure">Select which procedure they have had in the left breast</a></li>
                    <li><a href="#id_right_breast_other_surgery">Select any other surgery they have had in the right breast</a></li>
                    <li><a href="#id_left_breast_other_surgery">Select any other surgery they have had in the left breast</a></li>
                    <li><a href="#id_surgery_reason">Select the reason for surgery</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestUpdateMastectomyOrLumpectomyHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return MastectomyOrLumpectomyHistoryItemFactory.create(
            appointment=appointment,
            right_breast_procedure=MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
            left_breast_procedure=MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
            right_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY,
            ],
            left_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY,
            ],
            year_of_surgery=None,
            surgery_reason=MastectomyOrLumpectomyHistoryItem.SurgeryReason.RISK_REDUCTION,
            additional_details="",
        )

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_mastectomy_or_lumpectomy_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_mastectomy_or_lumpectomy_history_item",
                kwargs={"pk": appointment.pk, "history_item_pk": history_item.pk},
            ),
            {
                "right_breast_procedure": "NO_PROCEDURE",
                "left_breast_procedure": "NO_PROCEDURE",
                "right_breast_other_surgery": "NO_OTHER_SURGERY",
                "left_breast_other_surgery": "NO_OTHER_SURGERY",
                "surgery_reason": "RISK_REDUCTION",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated mastectomy or lumpectomy",
                )
            ],
        )
