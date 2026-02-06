import pytest

from manage_breast_screening.manual_images.models import Series
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)


@pytest.mark.django_db
class TestStudy:
    class TestHasSeriesWithMultipleImages:
        def test_returns_true_when_series_has_count_gt_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=2)

            assert study.has_series_with_multiple_images() is True

        def test_returns_false_when_all_series_have_count_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=1)
            SeriesFactory(study=study, count=1, laterality="L")

            assert study.has_series_with_multiple_images() is False

        def test_returns_false_when_no_series(self):
            study = StudyFactory()

            assert study.has_series_with_multiple_images() is False

        def test_returns_true_when_one_series_has_count_gt_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=1)
            SeriesFactory(study=study, count=3, laterality="L")

            assert study.has_series_with_multiple_images() is True

    class TestSeriesWithMultipleImages:
        def test_returns_only_series_with_count_gt_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=1, laterality="R", view_position="CC")
            series_2 = SeriesFactory(
                study=study, count=2, laterality="R", view_position="MLO"
            )
            series_3 = SeriesFactory(
                study=study, count=3, laterality="L", view_position="CC"
            )

            assert set(study.series_with_multiple_images()) == {series_2, series_3}

        def test_orders_by_laterality_then_view_position(self):
            study = StudyFactory()
            rmlo = SeriesFactory(
                study=study, count=2, laterality="R", view_position="MLO"
            )
            lmlo = SeriesFactory(
                study=study, count=2, laterality="L", view_position="MLO"
            )
            rcc = SeriesFactory(
                study=study, count=2, laterality="R", view_position="CC"
            )
            lcc = SeriesFactory(
                study=study, count=2, laterality="L", view_position="CC"
            )
            right_eklund = SeriesFactory(
                study=study, count=2, laterality="R", view_position="EKLUND"
            )
            left_eklund = SeriesFactory(
                study=study, count=2, laterality="L", view_position="EKLUND"
            )

            assert list(study.series_with_multiple_images()) == [
                rcc,
                rmlo,
                right_eklund,
                lcc,
                lmlo,
                left_eklund,
            ]

        def test_returns_empty_when_none(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=1)

            assert list(study.series_with_multiple_images()) == []


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
