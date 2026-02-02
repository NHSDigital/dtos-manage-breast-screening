from django import forms

from manage_breast_screening.manual_images.models import RepeatReason, RepeatType
from manage_breast_screening.nhsuk_forms.fields import (
    ChoiceField,
    IntegerField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields


class MultipleImagesInformationForm(FormWithConditionalFields):
    """
    Dynamic form for capturing information about multiple images for a given series.

    For each Series with count > 1, this form generates:
    - A repeat_type field (radio buttons) asking if additional images were repeats
    - A repeat_reasons field (checkboxes) for why repeats were needed
    - A repeat_count field (integer) for how many were repeats (only when count > 2)

    Field names are prefixed with the series identifier (e.g., rmlo_, lcc_).
    """

    def __init__(self, *args, series_list, instance, **kwargs):
        self.series_list = series_list
        self.instance = instance
        super().__init__(*args, **kwargs)

        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            self._add_fields_for_series(series, prefix)

    def _get_series_prefix(self, series):
        """Generate a field name prefix from the series laterality and view position."""
        return f"{series.laterality.lower()}{series.view_position.lower()}"

    def _add_fields_for_series(self, series, prefix):
        """Add repeat_type, repeat_reasons, and optionally repeat_count fields for a series."""
        repeat_type_field_name = f"{prefix}_repeat_type"
        repeat_reasons_field_name = f"{prefix}_repeat_reasons"
        repeat_count_field_name = f"{prefix}_repeat_count"

        # Build the radio choices based on image count
        if series.count == 2:
            choices = [
                (RepeatType.ALL_REPEATS.value, "Yes, it was a repeat"),
                (
                    RepeatType.NO_REPEATS.value,
                    "No, an extra image was needed to capture the complete view",
                ),
            ]
        else:
            choices = [
                (RepeatType.ALL_REPEATS.value, "Yes, all images were repeats"),
                (
                    RepeatType.SOME_REPEATS.value,
                    "Yes, some were repeats and some were extra images",
                ),
                (
                    RepeatType.NO_REPEATS.value,
                    "No, all extra images were needed to capture the complete view",
                ),
            ]

        self.fields[repeat_type_field_name] = ChoiceField(
            choices=choices,
            required=True,
            label="",
            label_classes="nhsuk-fieldset__legend--s nhsuk-u-visually-hidden",
            error_messages={
                "required": "Select whether the additional images were repeats"
            },
        )

        self.fields[repeat_reasons_field_name] = MultipleChoiceField(
            choices=RepeatReason.choices,
            required=False,
            label="Why were repeats needed?",
            label_classes="nhsuk-fieldset__legend--s",
            error_messages={"required": "Select why repeats were needed"},
        )

        # For count > 2, add repeat_count field
        if series.count > 2:
            additional_image_count = series.count - 1
            self.fields[repeat_count_field_name] = IntegerField(
                required=False,
                label="How many were repeats?",
                label_classes="nhsuk-label--s",
                classes="nhsuk-input--width-4",
                min_value=1,
                max_value=additional_image_count,
                error_messages={
                    "required": "Enter how many were repeats",
                    "min_value": "Number of repeats must be at least 1",
                    "max_value": f"Number of repeats must be at most {additional_image_count}",
                    "invalid": "Enter a valid number",
                },
            )

            # Set up conditional requirement for repeat_count
            self.given_field_value(
                repeat_type_field_name, RepeatType.SOME_REPEATS.value
            ).require_field(repeat_count_field_name)

        # Set initial values from the series
        if series.repeat_type:
            self.initial[repeat_type_field_name] = series.repeat_type
        if series.repeat_reasons:
            self.initial[repeat_reasons_field_name] = series.repeat_reasons
        if series.repeat_count is not None:
            self.initial[repeat_count_field_name] = series.repeat_count

    def clean(self):
        cleaned_data = super().clean()

        # Validate that repeat_reasons is provided when ALL_REPEATS or SOME_REPEATS is selected
        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            repeat_type = cleaned_data.get(f"{prefix}_repeat_type")
            repeat_reasons = cleaned_data.get(f"{prefix}_repeat_reasons")

            if repeat_type in (
                RepeatType.ALL_REPEATS.value,
                RepeatType.SOME_REPEATS.value,
            ):
                if not repeat_reasons:
                    self.add_error(
                        f"{prefix}_repeat_reasons",
                        forms.ValidationError(
                            message=self.fields[
                                f"{prefix}_repeat_reasons"
                            ].error_messages["required"],
                            code="required",
                        ),
                    )

        return cleaned_data

    def get_series_field_groups(self):
        """
        Return a list of (series, field_names_dict) tuples for template iteration.

        Each field_names_dict contains:
        - repeat_type: field name for the repeat type radio
        - repeat_reasons: field name for the reasons checkboxes
        - repeat_count: field name for the count (may be None if series.count == 2)
        """
        groups = []
        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            field_names = {
                "repeat_type": f"{prefix}_repeat_type",
                "repeat_reasons": f"{prefix}_repeat_reasons",
                "repeat_count": f"{prefix}_repeat_count" if series.count > 2 else None,
            }
            groups.append((series, field_names))
        return groups

    def update(self):
        """Save the repeat information to each Series."""
        for series in self.series_list:
            prefix = self._get_series_prefix(series)

            repeat_type = self.cleaned_data.get(f"{prefix}_repeat_type")
            series.repeat_type = repeat_type

            if repeat_type in (
                RepeatType.ALL_REPEATS.value,
                RepeatType.SOME_REPEATS.value,
            ):
                series.repeat_reasons = self.cleaned_data.get(
                    f"{prefix}_repeat_reasons", []
                )
            else:
                series.repeat_reasons = []

            if series.count > 2 and repeat_type == RepeatType.SOME_REPEATS.value:
                series.repeat_count = self.cleaned_data.get(f"{prefix}_repeat_count")
            else:
                series.repeat_count = None

            series.save()

        return self.instance
