import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    MastectomyOrLumpectomyHistoryItemFactory,
)

from ....forms.medical_history.mastectomy_or_lumpectomy_history_item_form import (
    MastectomyOrLumpectomyHistoryItemForm,
)


@pytest.mark.django_db
class TestMastectomyOrLumpectomyHistoryItemForm:
    @pytest.fixture
    def instance(self):
        return MastectomyOrLumpectomyHistoryItemFactory(
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

    def test_missing_required_fields(self):
        form = MastectomyOrLumpectomyHistoryItemForm(QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "right_breast_procedure": [
                "Select which procedure they have had in the right breast",
            ],
            "left_breast_procedure": [
                "Select which procedure they have had in the left breast",
            ],
            "right_breast_other_surgery": [
                "Select any other surgery they have had in the right breast",
            ],
            "left_breast_other_surgery": [
                "Select any other surgery they have had in the left breast",
            ],
            "surgery_reason": ["Select the reason for surgery"],
        }

    def test_right_breast_other_surgery_no_other_surgery_and_others(self):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                            MastectomyOrLumpectomyHistoryItem.Surgery.SYMMETRISATION,
                            MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY,
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
                    },
                    doseq=True,
                ),
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "right_breast_other_surgery": [
                'Unselect "No other surgery" in order to select other options'
            ],
        }

    def test_left_breast_other_surgery_no_other_surgery_and_others(self):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                            MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY,
                        ],
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
                    },
                    doseq=True,
                ),
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "left_breast_other_surgery": [
                'Unselect "No other surgery" in order to select other options'
            ],
        }

    @pytest.mark.parametrize(
        "year_of_surgery",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_year_of_surgery_outside_range(self, year_of_surgery):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "year_of_surgery": year_of_surgery,
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
                    },
                    doseq=True,
                ),
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "year_of_surgery": [
                self.create_year_outside_range_error_messsage(year_of_surgery)
            ],
        }

    def test_year_of_surgery_invalid(self):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "year_of_surgery": "invalid value for year_of_surgery",
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
                    },
                    doseq=True,
                ),
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "year_of_surgery": ["Enter a whole number."],
        }

    def test_other_reason_without_details(self):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                        ],
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON,
                    },
                    doseq=True,
                ),
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "surgery_other_reason_details": ["Provide details of the surgery"],
        }

    def test_other_reason_details_when_not_other_reason(self):
        appointment = AppointmentFactory()

        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                        "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                        "right_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                        ],
                        "left_breast_other_surgery": [
                            MastectomyOrLumpectomyHistoryItem.Surgery.SYMMETRISATION,
                        ],
                        "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
                        "surgery_other_reason_details": "surgery other details",
                    },
                    doseq=True,
                ),
            ),
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)
        obj.refresh_from_db()

        assert obj.appointment == appointment
        assert (
            obj.right_breast_procedure
            == MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY
        )
        assert (
            obj.left_breast_procedure
            == MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING
        )
        assert obj.right_breast_other_surgery == [
            MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
        ]
        assert obj.left_breast_other_surgery == [
            MastectomyOrLumpectomyHistoryItem.Surgery.SYMMETRISATION,
        ]
        assert obj.year_of_surgery is None
        assert (
            obj.surgery_reason
            == MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION
        )
        assert obj.surgery_other_reason_details == ""
        assert obj.additional_details == ""

    @pytest.mark.parametrize(
        "data",
        [
            {
                "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                "right_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                    MastectomyOrLumpectomyHistoryItem.Surgery.SYMMETRISATION,
                ],
                "left_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY,
                ],
                "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.RISK_REDUCTION,
            },
            {
                "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "right_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY
                ],
                "left_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION,
                    MastectomyOrLumpectomyHistoryItem.Surgery.SYMMETRISATION,
                ],
                "year_of_surgery": datetime.date.today().year - 80,
                "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.GENDER_AFFIRMATION,
            },
            {
                "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "right_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "left_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "year_of_surgery": datetime.date.today().year,
                "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON,
                "surgery_other_reason_details": "surgery other details",
                "additional_details": "additional details",
            },
        ],
    )
    def test_valid_create(self, clinical_user, data):
        appointment = AppointmentFactory()

        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(urlencode(data, doseq=True)),
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)
        obj.refresh_from_db()

        assert obj.appointment == appointment
        assert obj.right_breast_procedure == data.get("right_breast_procedure")
        assert obj.left_breast_procedure == data.get("left_breast_procedure")
        assert obj.right_breast_other_surgery == data.get("right_breast_other_surgery")
        assert obj.left_breast_other_surgery == data.get("left_breast_other_surgery")
        assert obj.year_of_surgery == data.get("year_of_surgery", None)
        assert obj.surgery_reason == data.get("surgery_reason", "")
        assert obj.surgery_other_reason_details == data.get(
            "surgery_other_reason_details", ""
        )
        assert obj.additional_details == data.get("additional_details", "")

    def create_year_outside_range_error_messsage(self, request_year):
        max_year = datetime.date.today().year
        min_year = max_year - 80
        return (
            (f"Year must be {max_year} or earlier")
            if request_year > max_year
            else (f"Year must be {min_year} or later")
        )

    @pytest.mark.parametrize(
        "data",
        [
            {
                "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                "right_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "left_breast_other_surgery": [
                    MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
                ],
                "year_of_surgery": datetime.date.today().year,
                "surgery_reason": MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON,
                "surgery_other_reason_details": "surgery other details",
                "additional_details": "additional details",
            },
        ],
    )
    def test_valid_update(self, instance, data):
        form = MastectomyOrLumpectomyHistoryItemForm(
            QueryDict(urlencode(data, doseq=True)),
            instance=instance,
        )

        assert form.is_valid()

        obj = form.update()

        obj.refresh_from_db()
        assert obj.appointment == instance.appointment
        assert obj.right_breast_procedure == data.get("right_breast_procedure")
        assert obj.left_breast_procedure == data.get("left_breast_procedure")
        assert obj.right_breast_other_surgery == data.get("right_breast_other_surgery")
        assert obj.left_breast_other_surgery == data.get("left_breast_other_surgery")
        assert obj.year_of_surgery == data.get("year_of_surgery", None)
        assert obj.surgery_reason == data.get("surgery_reason", "")
        assert obj.surgery_other_reason_details == data.get(
            "surgery_other_reason_details", ""
        )
        assert obj.additional_details == data.get("additional_details", "")
