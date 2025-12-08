from datetime import date
from urllib.parse import urlencode

import pytest
from django.forms import model_to_dict
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.mammograms.forms.breast_cancer_history_form import (
    BreastCancerHistoryForm,
    BreastCancerHistoryUpdateForm,
)
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastCancerHistoryItemFactory,
)


@pytest.fixture
def appointment():
    return AppointmentFactory()


@pytest.fixture
def incoming_request(clinical_user):
    request = RequestFactory().get("/test-form")
    request.user = clinical_user
    return request


class TestBreastCancerHistoryForm:
    def test_no_data_not_valid(self):
        form = BreastCancerHistoryForm(data=QueryDict())
        assert not form.is_valid()
        assert form.errors == {
            "diagnosis_location": ["Select which breasts cancer was diagnosed in"],
            "intervention_location": ["Select where surgery and treatment took place"],
            "left_breast_other_surgery": [
                "Select any other surgery they have had in the left breast"
            ],
            "left_breast_procedure": [
                "Select which procedure they have had in the left breast"
            ],
            "left_breast_treatment": [
                "Select what treatment they have had in the left breast"
            ],
            "right_breast_other_surgery": [
                "Select any other surgery they have had in the right breast"
            ],
            "right_breast_procedure": [
                "Select which procedure they have had in the right breast"
            ],
            "right_breast_treatment": [
                "Select what treatment they have had in the right breast"
            ],
            "systemic_treatments": ["Select what systemic treatments they have had"],
        }

    def test_valid_form(self, time_machine):
        time_machine.move_to(date(2025, 1, 1))

        form = BreastCancerHistoryForm(
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "diagnosis_year": "2013",
                        "intervention_location": "NHS_HOSPITAL",
                        "intervention_location_details_nhs_hospital": "abc",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
                    }
                )
            )
        )

        assert form.is_valid(), form.errors

    def test_invalid_date(self, time_machine):
        time_machine.move_to(date(2025, 1, 1))

        form = BreastCancerHistoryForm(
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "diagnosis_year": "1900",
                        "intervention_location": "NHS_HOSPITAL",
                        "intervention_location_details_nhs_hospital": "abc",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
                    }
                )
            )
        )

        assert not form.is_valid()
        assert form.errors == {"diagnosis_year": ["Year must be 1945 or later"]}

    def test_missing_intervention_location_details(self):
        form = BreastCancerHistoryForm(
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "intervention_location": "NHS_HOSPITAL",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
                    }
                )
            )
        )

        assert not form.is_valid()
        assert form.errors == {
            "intervention_location_details_nhs_hospital": [
                "Provide details about where the surgery and treatment took place"
            ],
        }

    def test_missing_systemic_treatments_other_treatment_details(self):
        form = BreastCancerHistoryForm(
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "intervention_location": "NHS_HOSPITAL",
                        "intervention_location_details_nhs_hospital": "abc",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "OTHER",
                    }
                )
            )
        )

        assert not form.is_valid()
        assert form.errors == {
            "systemic_treatments_other_treatment_details": [
                "Provide details of the other systemic treatment"
            ]
        }

    @pytest.mark.django_db
    def test_create(self, appointment, incoming_request):
        form = BreastCancerHistoryForm(
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "intervention_location": "NHS_HOSPITAL",
                        "intervention_location_details_nhs_hospital": "abc",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
                    }
                )
            )
        )
        assert form.is_valid()
        instance = form.create(appointment, incoming_request)

        assert model_to_dict(instance) == {
            "additional_details": "",
            "appointment": appointment.pk,
            "diagnosis_location": "RIGHT_BREAST",
            "diagnosis_year": None,
            "intervention_location": "NHS_HOSPITAL",
            "intervention_location_details": "abc",
            "left_breast_other_surgery": [
                "NO_SURGERY",
            ],
            "left_breast_procedure": "NO_PROCEDURE",
            "left_breast_treatment": [
                "NO_RADIOTHERAPY",
            ],
            "right_breast_other_surgery": [
                "LYMPH_NODE_SURGERY",
            ],
            "right_breast_procedure": "LUMPECTOMY",
            "right_breast_treatment": [
                "BREAST_RADIOTHERAPY",
            ],
            "systemic_treatments": [
                "NO_SYSTEMIC_TREATMENTS",
            ],
            "systemic_treatments_other_treatment_details": "",
        }


@pytest.mark.django_db
class TestBreastCancerHistoryUpdateForm:
    @pytest.fixture
    def instance(self, appointment):
        return BreastCancerHistoryItemFactory(
            appointment=appointment,
            diagnosis_location=BreastCancerHistoryItem.DiagnosisLocationChoices.BOTH_BREASTS,
            left_breast_procedure=BreastCancerHistoryItem.Procedure.LUMPECTOMY,
            right_breast_procedure=BreastCancerHistoryItem.Procedure.LUMPECTOMY,
        )

    def test_no_data_not_valid(self, instance):
        form = BreastCancerHistoryUpdateForm(instance=instance, data=QueryDict())
        assert not form.is_valid()
        assert form.errors == {
            "diagnosis_location": ["Select which breasts cancer was diagnosed in"],
            "intervention_location": ["Select where surgery and treatment took place"],
            "left_breast_other_surgery": [
                "Select any other surgery they have had in the left breast"
            ],
            "left_breast_procedure": [
                "Select which procedure they have had in the left breast"
            ],
            "left_breast_treatment": [
                "Select what treatment they have had in the left breast"
            ],
            "right_breast_other_surgery": [
                "Select any other surgery they have had in the right breast"
            ],
            "right_breast_procedure": [
                "Select which procedure they have had in the right breast"
            ],
            "right_breast_treatment": [
                "Select what treatment they have had in the right breast"
            ],
            "systemic_treatments": ["Select what systemic treatments they have had"],
        }

    def test_update(self, appointment, instance, incoming_request):
        form = BreastCancerHistoryUpdateForm(
            instance=instance,
            data=QueryDict(
                urlencode(
                    {
                        "diagnosis_location": "RIGHT_BREAST",
                        "intervention_location": "NHS_HOSPITAL",
                        "intervention_location_details_nhs_hospital": "abc",
                        "left_breast_other_surgery": "NO_SURGERY",
                        "left_breast_procedure": "NO_PROCEDURE",
                        "left_breast_treatment": "NO_RADIOTHERAPY",
                        "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                        "right_breast_procedure": "LUMPECTOMY",
                        "right_breast_treatment": "BREAST_RADIOTHERAPY",
                        "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
                    }
                )
            ),
        )
        assert form.is_valid()
        instance = form.update(incoming_request)

        assert model_to_dict(instance) == {
            "additional_details": "",
            "appointment": appointment.pk,
            "diagnosis_location": "RIGHT_BREAST",
            "diagnosis_year": None,
            "intervention_location": "NHS_HOSPITAL",
            "intervention_location_details": "abc",
            "left_breast_other_surgery": [
                "NO_SURGERY",
            ],
            "left_breast_procedure": "NO_PROCEDURE",
            "left_breast_treatment": [
                "NO_RADIOTHERAPY",
            ],
            "right_breast_other_surgery": [
                "LYMPH_NODE_SURGERY",
            ],
            "right_breast_procedure": "LUMPECTOMY",
            "right_breast_treatment": [
                "BREAST_RADIOTHERAPY",
            ],
            "systemic_treatments": [
                "NO_SYSTEMIC_TREATMENTS",
            ],
            "systemic_treatments_other_treatment_details": "",
        }
