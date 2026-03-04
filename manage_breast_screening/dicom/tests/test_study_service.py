from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.dicom.study_service import StudyService
from manage_breast_screening.dicom.tests.factories import (
    ImageFactory,
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory


class TestStudyService:
    @pytest.fixture
    def current_user(self):
        return MagicMock()

    @pytest.mark.django_db
    def test_save_success(self, current_user):
        gateway_action = GatewayActionFactory()
        study = StudyFactory(source_message_id=gateway_action.id)

        with patch.object(Auditor, "audit_update") as mock_audit_update:
            service = StudyService(gateway_action.appointment, current_user)
            result = service.save(
                additional_details="some details",
                imperfect_but_best_possible=True,
                reasons_incomplete=["reason"],
                reasons_incomplete_details="more details",
                completeness="complete",
            )

        assert result == study
        study.refresh_from_db()
        assert study.additional_details == "some details"
        assert study.imperfect_but_best_possible is True
        assert study.reasons_incomplete == ["reason"]
        assert study.reasons_incomplete_details == "more details"
        assert study.completeness == "complete"
        mock_audit_update.assert_called_once_with(study)

    @pytest.mark.django_db
    def test_save_no_action(self, current_user):
        service = StudyService(MagicMock(), current_user)
        result = service.save()
        assert result is None

    @pytest.mark.django_db
    def test_save_no_study(self, current_user):
        gateway_action = GatewayActionFactory()
        service = StudyService(gateway_action.appointment, current_user)
        result = service.save()
        assert result is None

    @pytest.mark.django_db
    def test_images_by_laterality_and_view(self):
        action = GatewayActionFactory()
        series = SeriesFactory.create(study__source_message_id=str(action.id))
        image1 = ImageFactory.create(series=series, view_position="CC", laterality="L")
        image2 = ImageFactory.create(series=series, view_position="CC", laterality="R")
        image3 = ImageFactory.create(series=series, view_position="MLO", laterality="L")
        image4 = ImageFactory.create(series=series, view_position="MLO", laterality="R")
        image5 = ImageFactory.create(series=series, view_position="MLO", laterality="R")

        assert StudyService.images_by_laterality_and_view(series.images.all()) == {
            "LCC": [image1],
            "LMLO": [image3],
            "RCC": [image2],
            "RMLO": [image4, image5],
        }

    @pytest.mark.django_db
    def test_image_counts_by_laterality_and_view(self):
        action = GatewayActionFactory()
        series = SeriesFactory.create(study__source_message_id=str(action.id))
        ImageFactory.create(series=series, view_position="CC", laterality="L")
        ImageFactory.create(series=series, view_position="CC", laterality="R")
        ImageFactory.create(series=series, view_position="MLO", laterality="L")
        ImageFactory.create(series=series, view_position="MLO", laterality="R")
        ImageFactory.create(series=series, view_position="MLO", laterality="R")

        assert StudyService.image_counts_by_laterality_and_view(
            series.images.all()
        ) == {
            "LCC": 1,
            "LMLO": 1,
            "RCC": 1,
            "RMLO": 2,
        }
