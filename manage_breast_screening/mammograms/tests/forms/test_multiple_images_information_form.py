import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.multiple_images_information_form import (
    MultipleImagesInformationForm,
)
from manage_breast_screening.manual_images.models import RepeatReason, RepeatType
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)


def make_query_dict(data: dict) -> QueryDict:
    """Convert a dict to a QueryDict, handling list values correctly."""
    qd = QueryDict(mutable=True)
    for key, value in data.items():
        if isinstance(value, list):
            qd.setlist(key, value)
        else:
            qd[key] = value
    return qd


@pytest.mark.django_db
class TestMultipleImagesInformationForm:
    class TestWithCount2:
        """Tests for series with count == 2 (single additional image)."""

        def test_no_data_requires_repeat_type(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="R", view_position="MLO", count=2
            )

            form = MultipleImagesInformationForm(
                QueryDict(), series_list=[series], instance=study
            )

            assert not form.is_valid()
            assert form.errors == {
                "rmlo_repeat_type": [
                    "Select whether the additional Right MLO images were repeats"
                ],
            }

        def test_all_repeats_requires_reasons(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="R", view_position="MLO", count=2
            )

            form = MultipleImagesInformationForm(
                make_query_dict({"rmlo_repeat_type": RepeatType.ALL_REPEATS.value}),
                series_list=[series],
                instance=study,
            )

            assert not form.is_valid()
            assert form.errors == {
                "rmlo_repeat_reasons": ["Select why repeats were needed"],
            }

        def test_no_repeats_does_not_require_reasons(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="R", view_position="MLO", count=2
            )

            form = MultipleImagesInformationForm(
                make_query_dict({"rmlo_repeat_type": RepeatType.NO_REPEATS.value}),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

        def test_all_repeats_with_reasons_saves_data(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="R", view_position="MLO", count=2
            )

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                        "rmlo_repeat_reasons": [
                            RepeatReason.PATIENT_MOVED.value,
                            RepeatReason.MOTION_BLUR.value,
                        ],
                    }
                ),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

            form.update()

            series.refresh_from_db()
            assert series.repeat_type == RepeatType.ALL_REPEATS.value
            assert series.repeat_reasons == [
                RepeatReason.PATIENT_MOVED.value,
                RepeatReason.MOTION_BLUR.value,
            ]
            assert series.repeat_count is None

    class TestWithCountGreaterThan2:
        """Tests for series with count > 2 (multiple additional images)."""

        def test_some_repeats_requires_count_and_reasons(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="L", view_position="CC", count=3
            )

            form = MultipleImagesInformationForm(
                make_query_dict({"lcc_repeat_type": RepeatType.SOME_REPEATS.value}),
                series_list=[series],
                instance=study,
            )

            assert not form.is_valid()
            assert "lcc_repeat_count" in form.errors
            assert "lcc_repeat_reasons" in form.errors

        def test_all_repeats_does_not_require_count(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="L", view_position="CC", count=3
            )

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "lcc_repeat_type": RepeatType.ALL_REPEATS.value,
                        "lcc_repeat_reasons": [RepeatReason.EQUIPMENT_FAULT.value],
                    }
                ),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

        def test_some_repeats_with_count_and_reasons_saves_data(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="L", view_position="CC", count=4
            )

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "lcc_repeat_type": RepeatType.SOME_REPEATS.value,
                        "lcc_repeat_count": 2,
                        "lcc_repeat_reasons": [RepeatReason.FOLDED_SKIN.value],
                    }
                ),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

            form.update()

            series.refresh_from_db()
            assert series.repeat_type == RepeatType.SOME_REPEATS.value
            assert series.repeat_count == 2
            assert series.repeat_reasons == [RepeatReason.FOLDED_SKIN.value]

        def test_no_repeats_clears_existing_all_repeats_data(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study,
                laterality="R",
                view_position="CC",
                count=3,
                repeat_type=RepeatType.ALL_REPEATS.value,
                repeat_reasons=[RepeatReason.PATIENT_MOVED.value],
            )

            form = MultipleImagesInformationForm(
                make_query_dict({"rcc_repeat_type": RepeatType.NO_REPEATS.value}),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

            form.update()

            series.refresh_from_db()
            assert series.repeat_type == RepeatType.NO_REPEATS.value
            assert series.repeat_reasons == []
            assert series.repeat_count is None

        def test_no_repeats_clears_existing_some_repeats_data(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study,
                laterality="R",
                view_position="CC",
                count=4,
                repeat_type=RepeatType.SOME_REPEATS.value,
                repeat_count=2,
                repeat_reasons=[RepeatReason.MOTION_BLUR.value],
            )

            form = MultipleImagesInformationForm(
                make_query_dict({"rcc_repeat_type": RepeatType.NO_REPEATS.value}),
                series_list=[series],
                instance=study,
            )

            assert form.is_valid()

            form.update()

            series.refresh_from_db()
            assert series.repeat_type == RepeatType.NO_REPEATS.value
            assert series.repeat_reasons == []
            assert series.repeat_count is None

        def test_repeat_count_max_value_validation(self):
            study = StudyFactory()
            series = SeriesFactory(
                study=study, laterality="L", view_position="MLO", count=4
            )

            # max_value should be count - 1 = 3
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "lmlo_repeat_type": RepeatType.SOME_REPEATS.value,
                        "lmlo_repeat_count": 4,  # Too high
                        "lmlo_repeat_reasons": [RepeatReason.OTHER.value],
                    }
                ),
                series_list=[series],
                instance=study,
            )

            assert not form.is_valid()
            assert "lmlo_repeat_count" in form.errors
            assert (
                "Number of repeats must be at most 3"
                in form.errors["lmlo_repeat_count"][0]
            )

    def test_multiple_series(self):
        study = StudyFactory()
        series1 = SeriesFactory(
            study=study, laterality="R", view_position="MLO", count=2
        )
        series2 = SeriesFactory(
            study=study, laterality="L", view_position="CC", count=3
        )

        form = MultipleImagesInformationForm(
            make_query_dict(
                {
                    "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                    "rmlo_repeat_reasons": [RepeatReason.PATIENT_MOVED.value],
                    "lcc_repeat_type": RepeatType.NO_REPEATS.value,
                }
            ),
            series_list=[series1, series2],
            instance=study,
        )

        assert form.is_valid()

        form.update()

        series1.refresh_from_db()
        series2.refresh_from_db()

        assert series1.repeat_type == RepeatType.ALL_REPEATS.value
        assert series1.repeat_reasons == [RepeatReason.PATIENT_MOVED.value]

        assert series2.repeat_type == RepeatType.NO_REPEATS.value
        assert series2.repeat_reasons == []

    def test_get_series_field_groups(self):
        study = StudyFactory()
        series1 = SeriesFactory(
            study=study, laterality="R", view_position="MLO", count=2
        )
        series2 = SeriesFactory(
            study=study, laterality="L", view_position="CC", count=3
        )

        form = MultipleImagesInformationForm(
            QueryDict(), series_list=[series1, series2], instance=study
        )

        groups = form.get_series_field_groups()

        assert len(groups) == 2

        # First series (count=2, no repeat_count field)
        series, fields = groups[0]
        assert series == series1
        assert fields["repeat_type"] == "rmlo_repeat_type"
        assert fields["repeat_reasons"] == "rmlo_repeat_reasons"
        assert fields["repeat_count"] is None

        # Second series (count=3, has repeat_count field)
        series, fields = groups[1]
        assert series == series2
        assert fields["repeat_type"] == "lcc_repeat_type"
        assert fields["repeat_reasons"] == "lcc_repeat_reasons"
        assert fields["repeat_count"] == "lcc_repeat_count"

    def test_initial_values_from_series(self):
        study = StudyFactory()
        series = SeriesFactory(
            study=study,
            laterality="R",
            view_position="MLO",
            count=3,
            repeat_type=RepeatType.SOME_REPEATS.value,
            repeat_count=1,
            repeat_reasons=[RepeatReason.MOTION_BLUR.value, RepeatReason.OTHER.value],
        )

        form = MultipleImagesInformationForm(series_list=[series], instance=study)

        assert form.initial["rmlo_repeat_type"] == RepeatType.SOME_REPEATS.value
        assert form.initial["rmlo_repeat_count"] == 1
        assert form.initial["rmlo_repeat_reasons"] == [
            RepeatReason.MOTION_BLUR.value,
            RepeatReason.OTHER.value,
        ]
