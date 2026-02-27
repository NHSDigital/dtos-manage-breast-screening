from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.images.image_details_form import (
    ImageDetailsForm,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.manual_images.models import (
    IncompleteImagesReason,
    Series,
    StudyCompleteness,
)
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.manual_images.tests.factories import StudyFactory


@pytest.fixture
def study_service(in_progress_appointment):
    return StudyService(appointment=in_progress_appointment, current_user=None)


@pytest.fixture
def recall_service(in_progress_appointment):
    return RecallService(appointment=in_progress_appointment, current_user=None)


@pytest.mark.django_db
class TestImageDetailsForm:
    def test_no_data(self):
        form = ImageDetailsForm(QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "rmlo_count": ["Enter the number of RMLO images"],
            "rcc_count": ["Enter the number of RCC images"],
            "right_eklund_count": ["Enter the number of Right Eklund images"],
            "lmlo_count": ["Enter the number of LMLO images"],
            "lcc_count": ["Enter the number of LCC images"],
            "left_eklund_count": ["Enter the number of Left Eklund images"],
        }

    def test_zero_images(self):
        form = ImageDetailsForm(
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
                        "not_all_mammograms_taken": False,
                        "reasons_incomplete": [],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": None,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "__all__": ["Enter at least one image count"],
        }

    def test_counts_provided_for_all_image_types(self, study_service, recall_service):
        rmlo_count = 7
        rcc_count = 5
        right_eklund_count = 20
        lmlo_count = 14
        lcc_count = 1
        left_eklund_count = 19
        additional_details = "Some additional details"
        form = ImageDetailsForm(
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
                        "not_all_mammograms_taken": False,
                        "reasons_incomplete": [],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": None,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert study.appointment == study_service.appointment
        assert study.additional_details == additional_details
        assert study.completeness == StudyCompleteness.COMPLETE
        assert not study.imperfect_but_best_possible
        assert study.reasons_incomplete == []

        series_list = study.series_set.all()
        assert len(series_list) == 6
        self._assert_series(series_list[0], "MLO", "R", rmlo_count)
        self._assert_series(series_list[1], "CC", "R", rcc_count)
        self._assert_series(series_list[2], "EKLUND", "R", right_eklund_count)
        self._assert_series(series_list[3], "MLO", "L", lmlo_count)
        self._assert_series(series_list[4], "CC", "L", lcc_count)
        self._assert_series(series_list[5], "EKLUND", "L", left_eklund_count)

    def test_counts_provided_for_only_one_image_type_and_should_recall(
        self, study_service, recall_service
    ):
        appointment = study_service.appointment
        lmlo_count = 1
        form = ImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": lmlo_count,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": True,
                        "reasons_incomplete": [
                            IncompleteImagesReason.LANGUAGE_OR_LEARNING_DIFFICULTIES,
                            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
                        ],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": ImageDetailsForm.RecallChoices.TO_BE_RECALLED,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert study.appointment == appointment
        assert study.completeness == StudyCompleteness.INCOMPLETE
        assert study.reasons_incomplete == [
            IncompleteImagesReason.LANGUAGE_OR_LEARNING_DIFFICULTIES,
            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
        ]
        assert study.reasons_incomplete_details == ""
        assert not study.imperfect_but_best_possible
        assert not study.additional_details
        assert appointment.reinvite

        series_list = study.series_set.all()
        assert len(series_list) == 1
        self._assert_series(series_list[0], "MLO", "L", lmlo_count)

    def test_counts_provided_for_only_one_image_type_and_should_not_recall(
        self, study_service, recall_service
    ):
        appointment = study_service.appointment
        lmlo_count = 1
        form = ImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": lmlo_count,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": True,
                        "reasons_incomplete": [
                            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE
                        ],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": True,
                        "should_recall": ImageDetailsForm.RecallChoices.PARTIAL_MAMMOGRAPHY,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert study.appointment == appointment
        assert study.completeness == StudyCompleteness.PARTIAL
        assert study.reasons_incomplete == [
            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
        ]
        assert study.reasons_incomplete_details == ""
        assert study.imperfect_but_best_possible
        assert not study.additional_details
        assert not appointment.reinvite

        series_list = study.series_set.all()
        assert len(series_list) == 1
        self._assert_series(series_list[0], "MLO", "L", lmlo_count)

    def test_not_all_mammograms_taken_but_not_marked_as_such(self):
        form = ImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 1,
                        "rcc_count": 1,
                        "right_eklund_count": 0,
                        "lmlo_count": 0,
                        "lcc_count": 1,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": False,
                        "reasons_incomplete": [],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": None,
                    },
                    doseq=True,
                )
            ),
        )
        assert not form.is_valid()
        assert form.errors == {
            "not_all_mammograms_taken": [
                'Select "Not all mammograms taken" if a CC or MLO view is missing'
            ]
        }

    def test_not_all_mammograms_taken_missing_reason(self):
        form = ImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 1,
                        "rcc_count": 1,
                        "right_eklund_count": 0,
                        "lmlo_count": 1,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": True,
                        "reasons_incomplete": [],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": ImageDetailsForm.RecallChoices.PARTIAL_MAMMOGRAPHY,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "reasons_incomplete": [
                "Select a reason why you could not take all the images"
            ]
        }

    def test_initial(self, in_progress_appointment):
        study = StudyFactory(
            appointment=in_progress_appointment,
            additional_details="important note",
            completeness=StudyCompleteness.INCOMPLETE,
            reasons_incomplete=[IncompleteImagesReason.TECHNICAL_ISSUES],
        )
        study.series_set.bulk_create(
            [
                Series(study=study, view_position="CC", laterality="L", count=1),
                Series(study=study, view_position="CC", laterality="R", count=0),
                Series(study=study, view_position="MLO", laterality="L", count=1),
                Series(study=study, view_position="MLO", laterality="R", count=1),
            ]
        )

        form = ImageDetailsForm(instance=study)

        assert form.initial == {
            "additional_details": "important note",
            "imperfect_but_best_possible": False,
            "lcc_count": 1,
            "left_eklund_count": 0,
            "lmlo_count": 1,
            "not_all_mammograms_taken": True,
            "rcc_count": 0,
            "reasons_incomplete": [
                IncompleteImagesReason.TECHNICAL_ISSUES,
            ],
            "reasons_incomplete_details": "",
            "right_eklund_count": 0,
            "rmlo_count": 1,
            "should_recall": ImageDetailsForm.RecallChoices.TO_BE_RECALLED,
        }

    def _assert_series(
        self, series, expected_view_position, expected_laterality, expected_count
    ):
        assert series.view_position == expected_view_position
        assert series.laterality == expected_laterality
        assert series.count == expected_count
