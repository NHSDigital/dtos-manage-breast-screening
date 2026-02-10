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


def get_fingerprint(instance):
    """Get the series fingerprint for testing."""
    form = MultipleImagesInformationForm(instance=instance)
    return form.initial["series_fingerprint"]


@pytest.mark.django_db
class TestMultipleImagesInformationForm:
    class TestWithCount2:
        """Tests for series with count == 2 (single additional image)."""

        def test_no_data_requires_repeat_type(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict({"series_fingerprint": fingerprint}),
                instance=study,
            )

            assert not form.is_valid()
            assert form.errors == {
                "rmlo_repeat_type": [
                    "Select whether the additional Right MLO images were repeats"
                ],
            }

        def test_all_repeats_requires_reasons(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert not form.is_valid()
            assert form.errors == {
                "rmlo_repeat_reasons": ["Select why repeats were needed"],
            }

        def test_no_repeats_does_not_require_reasons(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert form.is_valid()

        def test_all_repeats_with_reasons_saves_data(self):
            study = StudyFactory()
            series = SeriesFactory(study=study, rmlo=True, count=2)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                        "rmlo_repeat_reasons": [
                            RepeatReason.PATIENT_MOVED.value,
                            RepeatReason.MOTION_BLUR.value,
                        ],
                    }
                ),
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
            SeriesFactory(study=study, lcc=True, count=3)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "lcc_repeat_type": RepeatType.SOME_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert not form.is_valid()
            assert "lcc_repeat_count" in form.errors
            assert "lcc_repeat_reasons" in form.errors

        def test_all_repeats_does_not_require_count(self):
            study = StudyFactory()
            SeriesFactory(study=study, lcc=True, count=3)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "lcc_repeat_type": RepeatType.ALL_REPEATS.value,
                        "lcc_repeat_reasons": [RepeatReason.EQUIPMENT_FAULT.value],
                    }
                ),
                instance=study,
            )

            assert form.is_valid()

        def test_some_repeats_with_count_and_reasons_saves_data(self):
            study = StudyFactory()
            series = SeriesFactory(study=study, lcc=True, count=4)
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "lcc_repeat_type": RepeatType.SOME_REPEATS.value,
                        "lcc_repeat_count": 2,
                        "lcc_repeat_reasons": [RepeatReason.FOLDED_SKIN.value],
                    }
                ),
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
                rcc=True,
                count=3,
                repeat_type=RepeatType.ALL_REPEATS.value,
                repeat_reasons=[RepeatReason.PATIENT_MOVED.value],
            )
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rcc_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
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
                rcc=True,
                count=4,
                repeat_type=RepeatType.SOME_REPEATS.value,
                repeat_count=2,
                repeat_reasons=[RepeatReason.MOTION_BLUR.value],
            )
            fingerprint = get_fingerprint(study)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rcc_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
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
            SeriesFactory(study=study, lmlo=True, count=4)
            fingerprint = get_fingerprint(study)

            # max_value should be count - 1 = 3
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "lmlo_repeat_type": RepeatType.SOME_REPEATS.value,
                        "lmlo_repeat_count": 4,  # Too high
                        "lmlo_repeat_reasons": [RepeatReason.OTHER.value],
                    }
                ),
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
        series1 = SeriesFactory(study=study, rmlo=True, count=2)
        series2 = SeriesFactory(study=study, lcc=True, count=3)
        fingerprint = get_fingerprint(study)

        form = MultipleImagesInformationForm(
            make_query_dict(
                {
                    "series_fingerprint": fingerprint,
                    "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                    "rmlo_repeat_reasons": [RepeatReason.PATIENT_MOVED.value],
                    "lcc_repeat_type": RepeatType.NO_REPEATS.value,
                }
            ),
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
        series1 = SeriesFactory(study=study, rmlo=True, count=2)
        series2 = SeriesFactory(study=study, lcc=True, count=3)

        form = MultipleImagesInformationForm(QueryDict(), instance=study)

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
        SeriesFactory(
            study=study,
            rmlo=True,
            count=3,
            repeat_type=RepeatType.SOME_REPEATS.value,
            repeat_count=1,
            repeat_reasons=[RepeatReason.MOTION_BLUR.value, RepeatReason.OTHER.value],
        )

        form = MultipleImagesInformationForm(instance=study)

        assert form.initial["rmlo_repeat_type"] == RepeatType.SOME_REPEATS.value
        assert form.initial["rmlo_repeat_count"] == 1
        assert form.initial["rmlo_repeat_reasons"] == [
            RepeatReason.MOTION_BLUR.value,
            RepeatReason.OTHER.value,
        ]

    class TestStaleFormDetection:
        """Tests for stale form detection using series fingerprint."""

        def test_is_stale_returns_false_when_fingerprints_match(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)

            # Create form to get the fingerprint
            initial_form = MultipleImagesInformationForm(instance=study)
            fingerprint = initial_form.initial["series_fingerprint"]

            # Create form with submitted data including the fingerprint
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": fingerprint,
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert not form.is_stale()

        def test_is_stale_returns_true_when_series_count_changes(self):
            study = StudyFactory()
            series = SeriesFactory(study=study, rmlo=True, count=2)

            # Get fingerprint for original state
            initial_form = MultipleImagesInformationForm(instance=study)
            old_fingerprint = initial_form.initial["series_fingerprint"]

            # Change the series count
            series.count = 3
            series.save()

            # Form with old fingerprint submitted, but series has changed
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": old_fingerprint,
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert form.is_stale()

        def test_is_stale_returns_true_when_series_disappears(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)
            series2 = SeriesFactory(study=study, lcc=True, count=2)

            # Get fingerprint for original state (includes both series)
            initial_form = MultipleImagesInformationForm(instance=study)
            old_fingerprint = initial_form.initial["series_fingerprint"]

            # series2 drops to count=1 (no longer qualifies)
            series2.count = 1
            series2.save()

            # Form with old fingerprint, but series2 is no longer in list
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": old_fingerprint,
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert form.is_stale()

        def test_is_stale_returns_true_when_new_series_appears(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)

            # Get fingerprint for original state (only series1)
            initial_form = MultipleImagesInformationForm(instance=study)
            old_fingerprint = initial_form.initial["series_fingerprint"]

            # New series appears
            SeriesFactory(study=study, lcc=True, count=2)

            # Form with old fingerprint, but new series in DB
            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "series_fingerprint": old_fingerprint,
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert form.is_stale()

        def test_is_stale_returns_true_when_no_fingerprint_submitted(self):
            study = StudyFactory()
            SeriesFactory(study=study, rmlo=True, count=2)

            form = MultipleImagesInformationForm(
                make_query_dict(
                    {
                        "rmlo_repeat_type": RepeatType.NO_REPEATS.value,
                    }
                ),
                instance=study,
            )

            assert form.is_stale()
