from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.participants.models.cyst_history_item import (
    CystHistoryItem,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ...forms.cyst_history_form import CystHistoryForm


@pytest.mark.django_db
class TestCystHistoryItemForm:
    def test_no_data(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = CystHistoryForm(QueryDict(), participant=appointment.participant)

        assert not form.is_valid()
        assert form.errors == {"treatment": ["Select the treatment type"]}

    @pytest.mark.parametrize(
        "data",
        [
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
            },
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
                "additional_details": "Some additional details",
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
                "additional_details": "Some additional details",
            },
        ],
    )
    def test_success(self, clinical_user, data):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = CystHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment, request=request)

        assert obj.appointment == appointment
        assert obj.treatment == data.get("treatment")
        assert obj.additional_details == data.get("additional_details", "")
