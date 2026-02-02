import pytest

from manage_breast_screening.manual_images.models import Series
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)


@pytest.mark.django_db
class TestStudy:
    def test_has_series_with_multiple_images_returns_true_when_series_has_count_gt_1(
        self,
    ):
        study = StudyFactory()
        SeriesFactory(study=study, count=2)

        assert study.has_series_with_multiple_images() is True

    def test_has_series_with_multiple_images_returns_false_when_all_series_have_count_1(
        self,
    ):
        study = StudyFactory()
        SeriesFactory(study=study, count=1)
        SeriesFactory(study=study, count=1, laterality="L")

        assert study.has_series_with_multiple_images() is False

    def test_has_series_with_multiple_images_returns_false_when_no_series(self):
        study = StudyFactory()

        assert study.has_series_with_multiple_images() is False

    def test_has_series_with_multiple_images_returns_true_when_one_series_has_count_gt_1(
        self,
    ):
        study = StudyFactory()
        SeriesFactory(study=study, count=1)
        SeriesFactory(study=study, count=3, laterality="L")

        assert study.has_series_with_multiple_images() is True


class TestSeries:
    @pytest.mark.parametrize(
        "view_position,laterality,expected_string",
        [
            ("CC", "R", "RCC"),
            ("CC", "L", "LCC"),
            ("MLO", "R", "RMLO"),
            ("MLO", "L", "LMLO"),
            ("EKLUND", "R", "Right Eklund"),
            ("EKLUND", "L", "Left Eklund"),
            ("UNKNOWN", "X", "UNKNOWN X"),
        ],
    )
    def test_str_returns_expected_string(
        self, view_position, laterality, expected_string
    ):
        series = Series(view_position=view_position, laterality=laterality)
        assert str(series) == expected_string
