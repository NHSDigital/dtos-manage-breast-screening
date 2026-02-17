import json

from django import forms
from django.forms.widgets import Textarea

from manage_breast_screening.manual_images.models import RepeatReason, RepeatType
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
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

    additional_details = CharField(
        hint="Provide information for image readers when reviewing",
        required=False,
        label="Notes for reader (optional)",
        label_classes="nhsuk-label--s",
        widget=Textarea(attrs={"rows": 2}),
        max_words=500,
        error_messages={"max_words": "Notes for reader must be 500 words or less"},
    )

    def __init__(self, *args, instance, **kwargs):
        self.instance = instance
        self.series_list = list(instance.series_with_multiple_images())
        super().__init__(*args, **kwargs)
        self.initial["additional_details"] = self.instance.additional_details

        # Add hidden field for stale form detection
        self.fields["series_fingerprint"] = forms.CharField(
            widget=forms.HiddenInput(),
            required=True,
        )
        self.initial["series_fingerprint"] = self._get_series_fingerprint(
            self.series_list
        )

        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            self._add_fields_for_series(series, prefix)

    def is_stale(self):
        """Check if the submitted fingerprint matches the current series state."""
        submitted_fingerprint = self.data.get("series_fingerprint", "")
        current_fingerprint = self._get_series_fingerprint(self.series_list)
        return submitted_fingerprint != current_fingerprint

    def clean(self):
        cleaned_data = super().clean()

        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            repeat_type = cleaned_data.get(f"{prefix}_repeat_type")

            if repeat_type == RepeatType.ALL_REPEATS.value:
                reasons_field = f"{prefix}_all_repeats_reasons"
                if not cleaned_data.get(reasons_field):
                    self.add_error(
                        reasons_field,
                        forms.ValidationError(
                            message=self.fields[reasons_field].error_messages[
                                "required"
                            ],
                            code="required",
                        ),
                    )
            elif repeat_type == RepeatType.SOME_REPEATS.value:
                reasons_field = f"{prefix}_some_repeats_reasons"
                if not cleaned_data.get(reasons_field):
                    self.add_error(
                        reasons_field,
                        forms.ValidationError(
                            message=self.fields[reasons_field].error_messages[
                                "required"
                            ],
                            code="required",
                        ),
                    )

        return cleaned_data

    def get_series_field_groups(self):
        """
        Return a list of (series, field_names_dict) tuples for template iteration.

        Each field_names_dict contains:
        - repeat_type: field name for the repeat type radio
        - all_repeats_reasons: field name for the reasons checkboxes (ALL_REPEATS conditional)
        - some_repeats_reasons: field name for the reasons checkboxes (SOME_REPEATS conditional, or None)
        - repeat_count: field name for the count (may be None if series.count == 2)
        """
        groups = []
        for series in self.series_list:
            prefix = self._get_series_prefix(series)
            field_names = {
                "repeat_type": f"{prefix}_repeat_type",
                "all_repeats_reasons": f"{prefix}_all_repeats_reasons",
                "some_repeats_reasons": f"{prefix}_some_repeats_reasons"
                if series.count > 2
                else None,
                "repeat_count": f"{prefix}_repeat_count" if series.count > 2 else None,
            }
            groups.append((series, field_names))
        return groups

    def update(self, study_service: StudyService):
        """Save the repeat information to each Series and update study details."""
        for series in self.series_list:
            prefix = self._get_series_prefix(series)

            repeat_type = self.cleaned_data.get(f"{prefix}_repeat_type")
            series.repeat_type = repeat_type

            if repeat_type == RepeatType.ALL_REPEATS.value:
                series.repeat_reasons = self.cleaned_data.get(
                    f"{prefix}_all_repeats_reasons", []
                )
            elif repeat_type == RepeatType.SOME_REPEATS.value:
                series.repeat_reasons = self.cleaned_data.get(
                    f"{prefix}_some_repeats_reasons", []
                )
            else:
                series.repeat_reasons = []

            if series.count > 2 and repeat_type == RepeatType.SOME_REPEATS.value:
                series.repeat_count = self.cleaned_data.get(f"{prefix}_repeat_count")
            else:
                series.repeat_count = None

            series.save()

        study_service.update_additional_details(
            self.instance, self.cleaned_data.get("additional_details", "")
        )

        return self.instance

    def _add_fields_for_series(self, series, prefix):
        """Add repeat_type, repeat_reasons, and optionally repeat_count fields for a series."""
        repeat_type_field_name = f"{prefix}_repeat_type"
        all_repeats_reasons_field_name = f"{prefix}_all_repeats_reasons"
        some_repeats_reasons_field_name = f"{prefix}_some_repeats_reasons"
        repeat_count_field_name = f"{prefix}_repeat_count"

        # Build the radio choices based on image count
        series_name = str(series)
        if series.count == 2:
            question = "Was the additional image a repeat?"
            choices = [
                (RepeatType.ALL_REPEATS.value, "Yes, it was a repeat"),
                (
                    RepeatType.NO_REPEATS.value,
                    "No, an extra image was needed to capture the complete view",
                ),
            ]
        else:
            question = "Were the additional images repeats?"
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

        label = f"{series.count} {series_name} images were taken. {question}"

        self.fields[repeat_type_field_name] = ChoiceField(
            choices=choices,
            required=True,
            label=label,
            label_classes="nhsuk-fieldset__legend--m",
            error_messages={
                "required": f"Select whether the additional {series_name} image was a repeat"
                if series.count == 2
                else f"Select whether the additional {series_name} images were repeats"
            },
        )

        reasons_error_message = (
            f"Select why a repeat {series_name} image was needed"
            if series.count == 2
            else f"Select why {series_name} repeats were needed"
        )

        self.fields[all_repeats_reasons_field_name] = MultipleChoiceField(
            choices=RepeatReason.choices,
            required=False,
            label="Why were repeats needed?",
            hint="Select all that apply",
            label_classes="nhsuk-fieldset__legend--s",
            error_messages={"required": reasons_error_message},
        )

        # For count > 2, add a separate reasons field for the SOME_REPEATS
        # conditional panel to avoid duplicate DOM IDs
        if series.count > 2:
            self.fields[some_repeats_reasons_field_name] = MultipleChoiceField(
                choices=RepeatReason.choices,
                required=False,
                label="Why were repeats needed?",
                hint="Select all that apply",
                label_classes="nhsuk-fieldset__legend--s",
                error_messages={"required": reasons_error_message},
            )

            additional_image_count = series.count - 1
            self.fields[repeat_count_field_name] = IntegerField(
                required=False,
                label="How many were repeats?",
                label_classes="nhsuk-label--s",
                hint=f"Out of {additional_image_count} extra images",
                classes="nhsuk-input--width-4",
                min_value=1,
                max_value=additional_image_count,
                error_messages={
                    "required": f"Enter how many {series_name} images were repeats",
                    "min_value": f"Number of {series_name} repeats must be at least 1",
                    "max_value": f"Number of {series_name} repeats must be at most {additional_image_count}",
                    "invalid": f"Enter a valid number for {series_name} repeats",
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
            self.initial[all_repeats_reasons_field_name] = series.repeat_reasons
            if series.count > 2:
                self.initial[some_repeats_reasons_field_name] = series.repeat_reasons
        if series.repeat_count is not None:
            self.initial[repeat_count_field_name] = series.repeat_count

    def _get_series_prefix(self, series):
        """Generate a field name prefix from the series laterality and view position."""
        return f"{series.laterality.lower()}{series.view_position.lower()}"

    def _get_series_fingerprint(self, series_list):
        """Generate a fingerprint representing the current series state for stale form detection."""
        data = [(s.id.hex, s.laterality, s.view_position, s.count) for s in series_list]
        return json.dumps(data)
