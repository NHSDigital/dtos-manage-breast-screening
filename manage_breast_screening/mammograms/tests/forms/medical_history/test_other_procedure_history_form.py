import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    OtherProcedureHistoryItemFactory,
)

from ....forms.medical_history.other_procedure_history_form import (
    OtherProcedureHistoryForm,
)


@pytest.mark.django_db
class TestOtherProcedureHistoryForm:
    @pytest.fixture
    def instance(self):
        return OtherProcedureHistoryItemFactory(
            procedure=OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            procedure_details="Details of breast reduction",
        )

    def test_create_with_no_data(self):
        appointment = AppointmentFactory()
        form = OtherProcedureHistoryForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {"procedure": ["Select the procedure"]}

    def test_update_with_no_data(self, instance):
        appointment = AppointmentFactory()
        form = OtherProcedureHistoryForm(
            QueryDict(), instance=instance, participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {"procedure": ["Select the procedure"]}

    @pytest.mark.parametrize(
        "procedure,procedure_details_field",
        [
            (
                OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                "breast_reduction_details",
            ),
            (
                OtherProcedureHistoryItem.Procedure.BREAST_SYMMETRISATION,
                "breast_symmetrisation_details",
            ),
            (
                OtherProcedureHistoryItem.Procedure.NIPPLE_CORRECTION,
                "nipple_correction_details",
            ),
            (OtherProcedureHistoryItem.Procedure.OTHER, "other_details"),
        ],
    )
    def test_procedure_without_details(self, procedure, procedure_details_field):
        appointment = AppointmentFactory()

        form = OtherProcedureHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "procedure": procedure,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            procedure_details_field: ["Provide details of the procedure"]
        }

    def test_procedure_year_invalid_format(self):
        appointment = AppointmentFactory()

        form = OtherProcedureHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                        "breast_reduction_details": "Details of breast reduction",
                        "procedure_year": "invalid_year",
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": ["Enter a whole number."]}

    @pytest.mark.parametrize(
        "procedure_year",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_procedure_year_outside_range(self, procedure_year):
        appointment = AppointmentFactory()

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if procedure_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = OtherProcedureHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                        "breast_reduction_details": "Details of breast reduction",
                        "procedure_year": procedure_year,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": [year_outside_range_error_message]}

    success_test_cases = [
        {
            "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            "breast_reduction_details": "Details of breast reduction",
        },
        {
            "procedure": OtherProcedureHistoryItem.Procedure.BREAST_SYMMETRISATION,
            "breast_symmetrisation_details": "Details of breast symmetrisation",
            "procedure_year": datetime.date.today().year,
        },
        {
            "procedure": OtherProcedureHistoryItem.Procedure.NIPPLE_CORRECTION,
            "nipple_correction_details": "Details of nipple correction",
            "additional_details": "Some additional details",
        },
        {
            "procedure": OtherProcedureHistoryItem.Procedure.OTHER,
            "other_details": "Details of other procedure",
            "procedure_year": datetime.date.today().year - 80,
            "additional_details": "Some additional details",
        },
    ]

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_create_success(self, data, dummy_request):
        appointment = AppointmentFactory()
        form = OtherProcedureHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment, request=dummy_request)

        _assert_other_procedure_item(obj, appointment, data)

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_update_success(self, instance, data, dummy_request):
        appointment = AppointmentFactory()
        form = OtherProcedureHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
            instance=instance,
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.update(request=dummy_request)

        _assert_other_procedure_item(obj, instance.appointment, data)


def _assert_other_procedure_item(
    other_procedure_history_item, appointment, expected_data
):
    assert other_procedure_history_item.appointment == appointment
    assert other_procedure_history_item.procedure == expected_data.get("procedure")
    assert other_procedure_history_item.procedure_details == next(
        v
        for k, v in expected_data.items()
        if k != "additional_details" and k.endswith("_details")
    )
    assert other_procedure_history_item.procedure_year == expected_data.get(
        "procedure_year", None
    )
    assert other_procedure_history_item.additional_details == expected_data.get(
        "additional_details", ""
    )
