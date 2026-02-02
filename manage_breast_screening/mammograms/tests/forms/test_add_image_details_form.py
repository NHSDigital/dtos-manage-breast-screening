from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.add_image_details_form import (
    AddImageDetailsForm,
)
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
)


@pytest.mark.django_db
class TestAddImageDetailsForm:
    def test_no_data(self):
        form = AddImageDetailsForm(QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "rmlo_count": ["Enter the number of RMLO images."],
            "rcc_count": ["Enter the number of RCC images."],
            "right_eklund_count": ["Enter the number of Right Eklund images."],
            "lmlo_count": ["Enter the number of LMLO images."],
            "lcc_count": ["Enter the number of LCC images."],
            "left_eklund_count": ["Enter the number of Left Eklund images."],
        }

    def test_zero_images(self):
        form = AddImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": 0,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "additional_details": "Some additional details",
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "__all__": ["Enter at least one image count"],
        }

    def test_counts_provided_for_all_image_types(self):
        appointment = AppointmentFactory()
        rmlo_count = 7
        rcc_count = 5
        right_eklund_count = 20
        lmlo_count = 14
        lcc_count = 1
        left_eklund_count = 19
        additional_details = "Some additional details"
        form = AddImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": rmlo_count,
                        "rcc_count": rcc_count,
                        "right_eklund_count": right_eklund_count,
                        "lmlo_count": lmlo_count,
                        "lcc_count": lcc_count,
                        "left_eklund_count": left_eklund_count,
                        "additional_details": additional_details,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(StudyService(appointment=appointment, current_user=None))

        assert study.appointment == appointment
        assert study.additional_details == additional_details

        series_list = study.series_set.all()
        assert len(series_list) == 6
        self._assert_series(series_list[0], "MLO", "R", rmlo_count)
        self._assert_series(series_list[1], "CC", "R", rcc_count)
        self._assert_series(series_list[2], "EKLUND", "R", right_eklund_count)
        self._assert_series(series_list[3], "MLO", "L", lmlo_count)
        self._assert_series(series_list[4], "CC", "L", lcc_count)
        self._assert_series(series_list[5], "EKLUND", "L", left_eklund_count)

    def test_counts_provided_for_only_one_image_type(self):
        appointment = AppointmentFactory()
        lmlo_count = 1
        form = AddImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": lmlo_count,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(StudyService(appointment=appointment, current_user=None))

        assert study.appointment == appointment
        assert not study.additional_details

        series_list = study.series_set.all()
        assert len(series_list) == 1
        self._assert_series(series_list[0], "MLO", "L", lmlo_count)

    def _assert_series(
        self, series, expected_view_position, expected_laterality, expected_count
    ):
        assert series.view_position == expected_view_position
        assert series.laterality == expected_laterality
        assert series.count == expected_count
