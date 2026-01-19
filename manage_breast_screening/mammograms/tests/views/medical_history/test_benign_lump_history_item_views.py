from urllib.parse import urlencode

import pytest
from django.contrib import messages
from django.http import QueryDict
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BenignLumpHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddBenignLumpHistoryView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_benign_lump_history_item",
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
                "mammograms:add_benign_lump_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "left_breast_procedures": BenignLumpHistoryItem.Procedure.LUMP_REMOVED,
                "right_breast_procedures": BenignLumpHistoryItem.Procedure.NO_PROCEDURES,
                "procedure_location": BenignLumpHistoryItem.ProcedureLocation.EXACT_LOCATION_UNKNOWN,
                "exact_location_unknown_details": "abc",
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
                    message="Added benign lumps",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_benign_lump_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_left_breast_procedures">Select which procedures they have had in the left breast</a></li>
                    <li><a href="#id_right_breast_procedures">Select which procedures they have had in the right breast</a></li>
                    <li><a href="#id_procedure_location">Select where the tests and treatment were done</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeBenignLumpHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return BenignLumpHistoryItemFactory.create(appointment=appointment)

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_benign_lump_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_benign_lump_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
            ),
            QueryDict(
                urlencode(
                    {
                        "left_breast_procedures": [
                            BenignLumpHistoryItem.Procedure.NO_PROCEDURES
                        ],
                        "right_breast_procedures": [
                            BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY
                        ],
                        "procedure_location": BenignLumpHistoryItem.ProcedureLocation.EXACT_LOCATION_UNKNOWN,
                        "exact_location_unknown_details": "abc",
                    },
                    doseq=True,
                )
            ),
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": history_item.appointment_id},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated benign lumps",
                )
            ],
        )


@pytest.mark.django_db
class TestDeleteBenignLumpHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return BenignLumpHistoryItemFactory.create(appointment=appointment)

    def test_get_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_benign_lump_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_post_redirects_to_record_medical_information(
        self, clinical_user_client, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_benign_lump_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": history_item.appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Deleted benign lump",
                )
            ],
        )

    def test_the_history_item_is_deleted(self, clinical_user_client, history_item):
        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_benign_lump_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )

        assert not BenignLumpHistoryItem.objects.filter(pk=history_item.pk).exists()
