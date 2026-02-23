from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.dicom.models import Study
from manage_breast_screening.dicom.study_service import StudyService
from manage_breast_screening.dicom.tests.factories import ImageFactory, StudyFactory
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory
from manage_breast_screening.mammograms.forms.images.gateway_image_details_form import (
    GatewayImageDetailsForm,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.manual_images.models import (
    IncompleteImagesReason,
    StudyCompleteness,
)


@pytest.fixture
def study_service(in_progress_appointment):
    return StudyService(appointment=in_progress_appointment, current_user=None)


@pytest.fixture
def recall_service(in_progress_appointment):
    return RecallService(appointment=in_progress_appointment, current_user=None)


@pytest.mark.django_db
class TestGatewayImageDetailsForm:
    def test_no_data(self):
        form = GatewayImageDetailsForm(QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "rmlo_count": ["Enter the number of RMLO images"],
            "rcc_count": ["Enter the number of RCC images"],
            "lmlo_count": ["Enter the number of LMLO images"],
            "lcc_count": ["Enter the number of LCC images"],
        }

    def test_zero_images(self):
        form = GatewayImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "lmlo_count": 0,
                        "lcc_count": 0,
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
            "not_all_mammograms_taken": [
                'Select "Not all mammograms taken" if a CC or MLO view is missing'
            ],
        }

    def test_counts_provided_for_all_image_types(self, study_service, recall_service):
        gateway_action = GatewayActionFactory(appointment=study_service.appointment)
        StudyFactory(source_message_id=gateway_action.id)

        form = GatewayImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 7,
                        "rcc_count": 5,
                        "lmlo_count": 14,
                        "lcc_count": 1,
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

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert Study.for_appointment(study_service.appointment) == study
        assert study.additional_details == "Some additional details"
        assert study.completeness == StudyCompleteness.COMPLETE
        assert not study.imperfect_but_best_possible
        assert study.reasons_incomplete == []

    def test_counts_provided_for_only_one_image_type_and_should_recall(
        self, study_service, recall_service
    ):
        appointment = study_service.appointment
        gateway_action = GatewayActionFactory(appointment=appointment)
        StudyFactory(source_message_id=gateway_action.id)
        form = GatewayImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": 1,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": True,
                        "reasons_incomplete": [
                            IncompleteImagesReason.LANGUAGE_OR_LEARNING_DIFFICULTIES,
                            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
                        ],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": False,
                        "should_recall": GatewayImageDetailsForm.RecallChoices.TO_BE_RECALLED,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert study.completeness == StudyCompleteness.INCOMPLETE
        assert study.reasons_incomplete == [
            IncompleteImagesReason.LANGUAGE_OR_LEARNING_DIFFICULTIES,
            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
        ]
        assert study.reasons_incomplete_details == ""
        assert not study.imperfect_but_best_possible
        assert not study.additional_details
        assert appointment.reinvite

    def test_counts_provided_for_only_one_image_type_and_should_not_recall(
        self, study_service, recall_service
    ):
        gateway_action = GatewayActionFactory(appointment=study_service.appointment)
        StudyFactory(source_message_id=gateway_action.id)

        form = GatewayImageDetailsForm(
            QueryDict(
                urlencode(
                    {
                        "rmlo_count": 0,
                        "rcc_count": 0,
                        "right_eklund_count": 0,
                        "lmlo_count": 1,
                        "lcc_count": 0,
                        "left_eklund_count": 0,
                        "not_all_mammograms_taken": True,
                        "reasons_incomplete": [
                            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE
                        ],
                        "reasons_incomplete_details": "",
                        "imperfect_but_best_possible": True,
                        "should_recall": GatewayImageDetailsForm.RecallChoices.PARTIAL_MAMMOGRAPHY,
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        study = form.save(study_service=study_service, recall_service=recall_service)

        assert study.completeness == StudyCompleteness.PARTIAL
        assert study.reasons_incomplete == [
            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE,
        ]
        assert study.reasons_incomplete_details == ""
        assert study.imperfect_but_best_possible
        assert not study.additional_details
        assert not study_service.appointment.reinvite

    def test_not_all_mammograms_taken_but_not_marked_as_such(self):
        form = GatewayImageDetailsForm(
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
        form = GatewayImageDetailsForm(
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
                        "should_recall": GatewayImageDetailsForm.RecallChoices.PARTIAL_MAMMOGRAPHY,
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
        gateway_action = GatewayActionFactory(appointment=in_progress_appointment)
        study = StudyFactory(
            source_message_id=gateway_action.id,
            additional_details="important note",
            completeness=StudyCompleteness.INCOMPLETE,
            reasons_incomplete=[IncompleteImagesReason.TECHNICAL_ISSUES],
        )
        ImageFactory(series__study=study, laterality="R", view_position="MLO")
        ImageFactory(series__study=study, laterality="L", view_position="MLO")

        form = GatewayImageDetailsForm(instance=study)

        assert form.initial == {
            "additional_details": "important note",
            "imperfect_but_best_possible": False,
            "lmlo_count": 1,
            "lcc_count": 0,
            "not_all_mammograms_taken": True,
            "reasons_incomplete": [
                IncompleteImagesReason.TECHNICAL_ISSUES,
            ],
            "reasons_incomplete_details": "",
            "rmlo_count": 1,
            "rcc_count": 0,
            "should_recall": GatewayImageDetailsForm.RecallChoices.TO_BE_RECALLED,
        }
