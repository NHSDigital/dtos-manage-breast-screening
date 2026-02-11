import pytest

from manage_breast_screening.manual_images.models import (
    STANDARD_VIEWS_RCC_FIRST,
    ImageView,
    Series,
)
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)


@pytest.mark.django_db
class TestStudy:
    class TestHasSeriesWithMultipleImages:
        def test_returns_false_when_all_series_have_count_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, count=1, rcc=True)
            SeriesFactory(study=study, count=1, lcc=True)

            assert study.has_series_with_multiple_images() is False

        def test_returns_false_when_no_series(self):
            study = StudyFactory()

            assert study.has_series_with_multiple_images() is False

        def test_returns_true_when_at_least_one_series_has_count_gt_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, rcc=True, count=1)
            SeriesFactory(study=study, lcc=True, count=3)

            assert study.has_series_with_multiple_images() is True

    class TestSeriesWithMultipleImages:
        def test_returns_only_series_with_count_gt_1(self):
            study = StudyFactory()
            SeriesFactory(study=study, rcc=True, count=1)
            series_2 = SeriesFactory(study=study, rmlo=True, count=2)
            series_3 = SeriesFactory(study=study, lcc=True, count=3)

            assert set(study.series_with_multiple_images()) == {series_2, series_3}

        def test_orders_by_laterality_then_view_position(self):
            study = StudyFactory()
            rmlo = SeriesFactory(study=study, rmlo=True, count=2)
            lmlo = SeriesFactory(study=study, lmlo=True, count=2)
            rcc = SeriesFactory(study=study, rcc=True, count=2)
            lcc = SeriesFactory(study=study, lcc=True, count=2)
            right_eklund = SeriesFactory(study=study, right_eklund=True, count=2)
            left_eklund = SeriesFactory(study=study, left_eklund=True, count=2)

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


class TestImageView:
    @pytest.mark.parametrize("view", STANDARD_VIEWS_RCC_FIRST)
    def test_short_name_round_trip(self, view):
        assert ImageView.from_short_name(view.short_name) == view
