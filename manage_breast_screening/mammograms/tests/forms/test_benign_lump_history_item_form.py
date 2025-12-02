import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.mammograms.forms.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
)
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BenignLumpHistoryItemFactory,
)


def _form_data(data):
    return QueryDict(urlencode(data, doseq=True))


@pytest.mark.django_db
class TestBenignLumpHistoryItemForm:
    def test_missing_required_fields(self):
        form = BenignLumpHistoryItemForm(_form_data({}))

        assert not form.is_valid()
        assert form.errors == {
            "left_breast_procedures": [
                "Select which procedures they have had in the left breast"
            ],
            "right_breast_procedures": [
                "Select which procedures they have had in the right breast"
            ],
            "procedure_location": ["Select where the tests and treatment were done"],
        }

    @pytest.mark.parametrize(
        ("location", "detail_field"),
        tuple(BenignLumpHistoryItemForm.LOCATION_DETAIL_FIELDS.items()),
    )
    def test_requires_location_details_for_selected_location(
        self, location, detail_field
    ):
        form = BenignLumpHistoryItemForm(
            _form_data(
                [
                    (
                        "procedure_location",
                        location,
                    ),
                ]
            )
        )

        assert not form.is_valid()
        assert form.errors.get(detail_field) == [
            "Provide details about where the surgery and treatment took place"
        ]

    @pytest.mark.parametrize(
        ("procedure_year", "expected_message"),
        [
            (
                datetime.date.today().year - 80 - 1,
                f"Year must be {datetime.date.today().year - 80} or later",
            ),
            (
                datetime.date.today().year + 1,
                f"Year must be {datetime.date.today().year} or earlier",
            ),
        ],
    )
    def test_procedure_year_must_be_within_range(
        self, procedure_year, expected_message
    ):
        form = BenignLumpHistoryItemForm(
            _form_data(
                [
                    ("procedure_year", procedure_year),
                ]
            )
        )

        assert not form.is_valid()
        assert form.errors.get("procedure_year") == [expected_message]

    def test_create_persists_data(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().post("/test-form")
        request.user = clinical_user

        data = [
            (
                "left_breast_procedures",
                BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
            ),
            (
                "right_breast_procedures",
                BenignLumpHistoryItem.Procedure.NO_PROCEDURES,
            ),
            ("procedure_year", datetime.date.today().year - 1),
            (
                "procedure_location",
                BenignLumpHistoryItem.ProcedureLocation.NHS_HOSPITAL,
            ),
            ("nhs_hospital_details", "St Thomas' Hospital"),
            ("additional_details", "Additional details."),
        ]
        form = BenignLumpHistoryItemForm(_form_data(data))
        assert form.is_valid()

        obj = form.create(appointment=appointment, request=request)

        obj.refresh_from_db()
        assert obj.appointment == appointment
        assert obj.left_breast_procedures == [
            BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY
        ]
        assert obj.right_breast_procedures == [
            BenignLumpHistoryItem.Procedure.NO_PROCEDURES
        ]
        assert obj.procedure_year == data[2][1]
        assert obj.procedure_location == (
            BenignLumpHistoryItem.ProcedureLocation.NHS_HOSPITAL
        )
        assert obj.procedure_location_details == "St Thomas' Hospital"
        assert obj.additional_details == "Additional details."

    def test_initial_values_populated_from_instance(self):
        instance = BenignLumpHistoryItemFactory(
            left_breast_procedures=[
                BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
                BenignLumpHistoryItem.Procedure.LUMP_REMOVED,
            ],
            right_breast_procedures=[BenignLumpHistoryItem.Procedure.NO_PROCEDURES],
            procedure_year=2020,
            procedure_location=BenignLumpHistoryItem.ProcedureLocation.OUTSIDE_UK,
            procedure_location_details="Hospital in France",
            additional_details="Some additional notes",
        )

        form = BenignLumpHistoryItemForm(instance=instance)

        assert form.initial["left_breast_procedures"] == [
            BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
            BenignLumpHistoryItem.Procedure.LUMP_REMOVED,
        ]
        assert form.initial["right_breast_procedures"] == [
            BenignLumpHistoryItem.Procedure.NO_PROCEDURES
        ]
        assert form.initial["procedure_year"] == 2020
        assert form.initial["procedure_location"] == (
            BenignLumpHistoryItem.ProcedureLocation.OUTSIDE_UK
        )
        assert form.initial["outside_uk_details"] == "Hospital in France"
        assert form.initial["additional_details"] == "Some additional notes"

    def test_update_persists_changes(self, clinical_user):
        instance = BenignLumpHistoryItemFactory(
            left_breast_procedures=[BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY],
            right_breast_procedures=[BenignLumpHistoryItem.Procedure.NO_PROCEDURES],
            procedure_year=2020,
            procedure_location=BenignLumpHistoryItem.ProcedureLocation.NHS_HOSPITAL,
            procedure_location_details="Original Hospital",
            additional_details="Original details",
        )
        request = RequestFactory().post("/test-form")
        request.user = clinical_user

        data = [
            ("left_breast_procedures", BenignLumpHistoryItem.Procedure.LUMP_REMOVED),
            (
                "right_breast_procedures",
                BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
            ),
            ("procedure_year", 2021),
            (
                "procedure_location",
                BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK,
            ),
            ("private_clinic_uk_details", "Private Hospital Updated"),
            ("additional_details", "Updated details"),
        ]
        form = BenignLumpHistoryItemForm(_form_data(data), instance=instance)
        assert form.is_valid()
        updated_obj = form.update(request=request)
        assert updated_obj.pk == instance.pk
        assert updated_obj.left_breast_procedures == [
            BenignLumpHistoryItem.Procedure.LUMP_REMOVED
        ]
        assert updated_obj.right_breast_procedures == [
            BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY
        ]
        assert updated_obj.procedure_year == 2021
        assert updated_obj.procedure_location == (
            BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK
        )
        assert updated_obj.procedure_location_details == "Private Hospital Updated"
        assert updated_obj.additional_details == "Updated details"
