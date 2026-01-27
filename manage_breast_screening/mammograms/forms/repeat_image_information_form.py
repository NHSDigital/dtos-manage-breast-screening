from django.forms import Textarea

from manage_breast_screening.manual_images.models import RepeatReason, RepeatType
from manage_breast_screening.nhsuk_forms.fields import CharField
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
    RadioSelectWithoutFieldset,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields

LATERALITY_LABELS = {"L": "Left", "R": "Right"}


def _field_prefix(series):
    """Generate the field name prefix for a series, e.g. 'rmlo' or 'lcc'."""
    return f"{series.laterality.lower()}{series.view_position.lower()}"


def _series_label(series):
    """Generate a human-readable label for a series, e.g. 'Right MLO'."""
    laterality_label = LATERALITY_LABELS.get(series.laterality, series.laterality)
    return f"{laterality_label} {series.view_position}"


class RepeatImageInformationForm(FormWithConditionalFields):
    """
    Dynamic form for capturing repeat image information for Series with count > 1.

    For each qualifying Series, generates a pair of fields:
    - {prefix}_is_repeat: Radio field asking if the additional image was a repeat
    - {prefix}_reasons: Checkbox field for selecting repeat reasons (shown conditionally)
    """

    additional_details = CharField(
        label="Additional details (optional)",
        label_classes="nhsuk-label--m",
        required=False,
        widget=Textarea(attrs={"rows": 4}),
        max_words=500,
        error_messages={"max_words": "Additional details must be 500 words or less"},
    )

    def __init__(self, *args, instance=None, series_list=None, **kwargs):
        self.instance = instance  # Study object
        self.series_list = series_list or []

        if instance:
            kwargs.setdefault("initial", {})
            kwargs["initial"]["additional_details"] = instance.additional_details

            for series in self.series_list:
                prefix = _field_prefix(series)
                if series.is_repeat:
                    kwargs["initial"][f"{prefix}_is_repeat"] = series.is_repeat
                if series.repeat_reasons:
                    kwargs["initial"][f"{prefix}_reasons"] = series.repeat_reasons

        super().__init__(*args, **kwargs)

        for series in self.series_list:
            self._add_fields_for_series(series)

    def _add_fields_for_series(self, series):
        """Add is_repeat radio and reasons checkbox fields for a single Series."""
        prefix = _field_prefix(series)
        series_label = _series_label(series)

        # For count == 2, use YES_REPEAT/NO_EXTRA_NEEDED options
        # For count > 2, use ALL_REPEATS/SOME_REPEATS/ALL_EXTRA options
        if series.count == 2:
            is_repeat_choices = [
                (RepeatType.YES_REPEAT.value, RepeatType.YES_REPEAT.label),
                (RepeatType.NO_EXTRA_NEEDED.value, RepeatType.NO_EXTRA_NEEDED.label),
            ]
            repeat_predicate_values = [RepeatType.YES_REPEAT.value]
        else:
            is_repeat_choices = [
                (RepeatType.ALL_REPEATS.value, RepeatType.ALL_REPEATS.label),
                (RepeatType.SOME_REPEATS.value, RepeatType.SOME_REPEATS.label),
                (RepeatType.ALL_EXTRA.value, RepeatType.ALL_EXTRA.label),
            ]
            repeat_predicate_values = [
                RepeatType.ALL_REPEATS.value,
                RepeatType.SOME_REPEATS.value,
            ]

        is_repeat_field = ChoiceField(
            label=f"Was the additional {series_label} image a repeat?",
            choices=is_repeat_choices,
            widget=RadioSelectWithoutFieldset,
            error_messages={
                "required": f"Select whether the additional {series_label} image was a repeat"
            },
        )
        self.fields[f"{prefix}_is_repeat"] = is_repeat_field

        reasons_field = MultipleChoiceField(
            label="Why was the image repeated?",
            hint="Select all that apply",
            choices=RepeatReason.choices,
            error_messages={
                "required": f"Select why the {series_label} image was repeated"
            },
        )
        self.fields[f"{prefix}_reasons"] = reasons_field

        # Make reasons conditionally required when a repeat option is selected
        for predicate_value in repeat_predicate_values:
            self.given_field_value(
                f"{prefix}_is_repeat", predicate_value
            ).require_field(f"{prefix}_reasons")

    def get_series_field_groups(self):
        """Return list of (series, is_repeat_field_name, reasons_field_name) tuples."""
        return [
            (
                series,
                f"{_field_prefix(series)}_is_repeat",
                f"{_field_prefix(series)}_reasons",
            )
            for series in self.series_list
        ]

    def update(self):
        """Save repeat information to each Series and additional_details to Study."""
        if self.instance is None:
            raise ValueError("Form has no instance")

        # Update each Series
        for series in self.series_list:
            prefix = _field_prefix(series)
            series.is_repeat = self.cleaned_data.get(f"{prefix}_is_repeat")
            series.repeat_reasons = self.cleaned_data.get(f"{prefix}_reasons", [])
            series.save(update_fields=["is_repeat", "repeat_reasons", "updated_at"])

        # Update Study additional_details
        self.instance.additional_details = self.cleaned_data.get(
            "additional_details", ""
        )
        self.instance.save(update_fields=["additional_details", "updated_at"])

        return self.instance
