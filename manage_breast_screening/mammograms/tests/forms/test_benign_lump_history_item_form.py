import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.mammograms.forms.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
)
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


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

    def test_create_persists_data_and_audits(self, clinical_user):
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

        existing_log_count = AuditLog.objects.count()
        obj = form.create(appointment=appointment, request=request)
        assert AuditLog.objects.count() == existing_log_count + 1
        audit_log = AuditLog.objects.filter(
            object_id=obj.pk, operation=AuditLog.Operations.CREATE
        ).first()
        assert audit_log.actor == clinical_user

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
