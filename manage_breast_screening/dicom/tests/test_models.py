import pytest

from manage_breast_screening.dicom.models import Study
from manage_breast_screening.dicom.tests.factories import (
    ImageFactory,
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory


@pytest.mark.django_db
class TestStudy:
    def test_study_has_series_with_multiple_images(self):
        series = SeriesFactory.create()
        ImageFactory.create_batch(2, series=series)
        study = series.study

        assert study.has_series_with_multiple_images() is True

    def test_study_series_with_multiple_images_only_counts_series_with_more_than_one_image(
        self,
    ):
        series = SeriesFactory.create()
        ImageFactory.create_batch(2, series=series)
        ImageFactory.create(series=series)
        study = series.study

        assert study.series_with_multiple_images().count() == 1

    def test_study_does_not_have_series_with_multiple_images(self):
        study = StudyFactory.create()
        ImageFactory.create(series__study=study)

        assert study.has_series_with_multiple_images() is False

    def test_study_for_appointment(self):
        study = StudyFactory.create()
        action = GatewayActionFactory.create(id=study.source_message_id)

        assert Study.for_appointment(action.appointment) == study


@pytest.mark.django_db
class TestSeries:
    def test_series_count_property(self):
        series = SeriesFactory.create()
        ImageFactory.create_batch(3, series=series)

        assert series.count == 3

    def test_series_extra_count_property(self):
        series = SeriesFactory.create()
        ImageFactory.create(series=series)
        ImageFactory.create(series=series, implant_present=True)

        assert series.extra_count == 1

    def test_series_laterality(self):
        series = SeriesFactory.create()
        ImageFactory.create(series=series, laterality="R")

        assert series.laterality == "R"

    def test_series_laterality_no_images(self):
        series = SeriesFactory.create()

        assert series.laterality == ""

    def test_series_view_position(self):
        series = SeriesFactory.create()
        ImageFactory.create(series=series, view_position="MLO")

        assert series.view_position == "MLO"

    def test_series_view_position_no_images(self):
        series = SeriesFactory.create()

        assert series.view_position == ""


@pytest.mark.django_db
class TestImage:
    @pytest.mark.parametrize(
        "laterality, view_position, expected",
        [
            ("R", "MLO", "RMLO"),
            ("R", "CC", "RCC"),
            ("L", "MLO", "LMLO"),
            ("L", "CC", "LCC"),
            ("R", "", ""),
            ("", "MLO", ""),
            ("", "", ""),
        ],
    )
    def test_laterality_and_view(self, laterality, view_position, expected):
        image = ImageFactory.build(laterality=laterality, view_position=view_position)

        assert image.laterality_and_view == expected

    def test_image_str_representation(self):
        image = ImageFactory.build(laterality="R", view_position="MLO")
        assert str(image) == "RMLO"
