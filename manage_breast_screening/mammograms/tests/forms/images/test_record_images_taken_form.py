from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.images.record_images_taken_form import (
    RecordImagesTakenForm,
)
from manage_breast_screening.manual_images.services import StudyService


@pytest.fixture
def mock_study_service():
    return MagicMock(spec=StudyService)


def test_invalid_form():
    form = RecordImagesTakenForm(QueryDict())
    assert not form.is_valid()
    assert form.errors == {
        "standard_images": [
            "Select whether you have taken a standard set of images or not"
        ]
    }


def test_valid_form():
    form = RecordImagesTakenForm(
        QueryDict(
            urlencode(
                {
                    "standard_images": RecordImagesTakenForm.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO
                }
            )
        )
    )
    assert form.is_valid()


def test_save_with_yes_answer(mock_study_service):
    form = RecordImagesTakenForm(
        QueryDict(
            urlencode(
                {
                    "standard_images": RecordImagesTakenForm.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO
                }
            )
        )
    )
    form.is_valid()
    form.save(mock_study_service)

    mock_study_service.create_with_default_series.assert_called_once()


def test_save_with_no_add_additional_answer(mock_study_service):
    form = RecordImagesTakenForm(
        QueryDict(
            urlencode(
                {
                    "standard_images": RecordImagesTakenForm.StandardImagesChoices.NO_ADD_ADDITIONAL
                }
            )
        )
    )
    form.is_valid()
    form.save(mock_study_service)

    mock_study_service.delete_if_exists.assert_not_called()


def test_save_with_no_images_taken_answer(mock_study_service):
    form = RecordImagesTakenForm(
        QueryDict(
            urlencode(
                {
                    "standard_images": RecordImagesTakenForm.StandardImagesChoices.NO_IMAGES_TAKEN
                }
            )
        )
    )
    form.is_valid()
    form.save(mock_study_service)

    mock_study_service.delete_if_exists.assert_called_once()
