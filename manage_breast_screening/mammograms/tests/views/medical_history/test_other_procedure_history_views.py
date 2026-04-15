import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    OtherProcedureHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddOtherProcedureView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_other_procedure_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_other_procedure_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                "breast_reduction_details": "Details of breast reduction",
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
                    message="Added other procedures",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_other_procedure_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_procedure">Select the procedure</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeOtherProcedureView:
    @pytest.fixture
    def history_item(self, confirmed_identity_appointment):
        return OtherProcedureHistoryItemFactory.create(
            appointment=confirmed_identity_appointment,
            procedure=OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            procedure_details="Initial details",
        )

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_other_procedure_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_record_medical_information(
        self, clinical_user_client, confirmed_identity_appointment, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_other_procedure_history_item",
                kwargs={
                    "pk": confirmed_identity_appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            ),
            {
                "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                "breast_reduction_details": "Updated details of breast reduction",
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
                    message="Updated other procedures",
                )
            ],
        )

    def test_the_other_procedure_is_deleted(self, clinical_user_client, history_item):
        assert OtherProcedureHistoryItem.objects.filter(pk=history_item.pk).exists()

        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_other_procedure_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )

        assert not OtherProcedureHistoryItem.objects.filter(pk=history_item.pk).exists()
