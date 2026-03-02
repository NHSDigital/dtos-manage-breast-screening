import json
import logging

from django import forms
from django.http import QueryDict

from manage_breast_screening.dicom.study_service import StudyService
from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.manual_images.models import (
    RepeatReason,
    RepeatType,
    StudyCompleteness,
)
from manage_breast_screening.nhsuk_forms.fields import (
    ChoiceField,
    IntegerField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)

from .gateway_images_form_fields_mixin import (
    GatewayImagesFormFieldsMixin,
    RecallChoices,
)

logger = logging.getLogger(__name__)


class GatewayImageDetailsForm(GatewayImagesFormFieldsMixin, FormWithConditionalFields):
    def __init__(self, *args, instance=None, **kwargs):
        if instance:
            images = instance.images().all()
            grouped_images = StudyService.images_by_laterality_and_view(images)

            self.instance = instance
            self.series_list = list(instance.series_with_multiple_images())

            super().__init__(*args, **kwargs)

            self.initial["imperfect_but_best_possible"] = (
                instance.imperfect_but_best_possible
            )
            self.initial["not_all_mammograms_taken"] = bool(instance.reasons_incomplete)
            self.initial["reasons_incomplete"] = instance.reasons_incomplete
            self.initial["reasons_incomplete_details"] = (
                instance.reasons_incomplete_details
            )
            self.initial["should_recall"] = self.recall_choice(instance.completeness)
            self.initial["lmlo_count"] = len(grouped_images["LMLO"])
            self.initial["lcc_count"] = len(grouped_images["LCC"])
            self.initial["rmlo_count"] = len(grouped_images["RMLO"])
            self.initial["rcc_count"] = len(grouped_images["RCC"])
            self.initial["additional_details"] = instance.additional_details

            self.given_field_value("not_all_mammograms_taken", True).require_field(
                "reasons_incomplete"
            )
            self.given_field_value("not_all_mammograms_taken", True).require_field(
                "should_recall"
            )
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

        else:
            self.series_list = []
            kwargs["initial"] = {
                "imperfect_but_best_possible": None,
                "not_all_mammograms_taken": None,
                "reasons_incomplete": None,
                "reasons_incomplete_details": None,
                "should_recall": None,
                "lmlo_count": 0,
                "lcc_count": 0,
                "rmlo_count": 0,
                "rcc_count": 0,
                "additional_details": None,
            }
            super().__init__(*args, **kwargs)

    def recall_choice(self, completeness):
        match completeness:
            case StudyCompleteness.INCOMPLETE:
                return RecallChoices.TO_BE_RECALLED
            case StudyCompleteness.PARTIAL:
                return RecallChoices.PARTIAL_MAMMOGRAPHY
            case _:
                return None

    def clean(self):
        cleaned_data = super().clean()
        not_all_mammograms_taken = self.cleaned_data.get("not_all_mammograms_taken")

        if (
            self.cleaned_data.get("rmlo_count") == 0
            and self.cleaned_data.get("rcc_count") == 0
            and self.cleaned_data.get("lmlo_count") == 0
            and self.cleaned_data.get("lcc_count") == 0
        ):
            self.add_error(None, "Enter at least one image count")
        elif (
            any(
                self.cleaned_data.get(f"{view}_count") == 0
                for view in ("rmlo", "rcc", "lmlo", "lcc")
            )
            and not not_all_mammograms_taken
        ):
            self.add_error(
                "not_all_mammograms_taken",
                'Select "Not all mammograms taken" if a CC or MLO view is missing',
            )

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

    def completeness(self):
        match self.cleaned_data.get("should_recall"):
            case RecallChoices.TO_BE_RECALLED:
                return StudyCompleteness.INCOMPLETE
            case RecallChoices.PARTIAL_MAMMOGRAPHY:
                return StudyCompleteness.PARTIAL
            case _:
                return StudyCompleteness.COMPLETE

    def save(self, study_service: StudyService, recall_service: RecallService):
        """Save the repeat information to each Series and update study details."""
        study = study_service.save(
            additional_details=self.cleaned_data.get("additional_details", ""),
            imperfect_but_best_possible=self.cleaned_data.get(
                "imperfect_but_best_possible", False
            ),
            reasons_incomplete=self.cleaned_data.get("reasons_incomplete", []),
            reasons_incomplete_details=self.cleaned_data.get(
                "reasons_incomplete_details", ""
            ),
            completeness=self.completeness(),
        )

        if self.cleaned_data["should_recall"] == RecallChoices.TO_BE_RECALLED:
            recall_service.reinvite()

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
            elif series.count >= 2 and repeat_type == RepeatType.ALL_REPEATS.value:
                series.repeat_count = series.count - 1
            else:
                series.repeat_count = None

            series.save()

        return study

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )

    def is_stale(self):
        """Check if the submitted fingerprint matches the current series state."""
        submitted_fingerprint = self.data.get("series_fingerprint", "")
        current_fingerprint = self._get_series_fingerprint(self.series_list)
        return submitted_fingerprint != current_fingerprint

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
        # conditional checkboxes to avoid duplicate DOM IDs
        if series.count > 2:
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

            self.fields[some_repeats_reasons_field_name] = MultipleChoiceField(
                choices=RepeatReason.choices,
                required=False,
                label="Why were repeats needed?",
                hint="Select all that apply",
                label_classes="nhsuk-fieldset__legend--s",
                error_messages={"required": reasons_error_message},
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

    @staticmethod
    def streamed_form_params(request_params: QueryDict, grouped_images):
        """Return a dict of series instance UIDs to their repetition details for streaming to the backend."""
        params = {}
        for key in request_params:
            if key.endswith("_repeat_type"):
                params[key] = request_params.get(key)
                params[key.replace("_repeat_type", "_all_repeats_reasons")] = []
            if key.endswith("_all_repeats_reasons"):
                params[key] = request_params.getlist(key)
        for view, images in grouped_images.items():
            params[f"{view.lower()}_count"] = len(images)
        return params

    def _get_series_prefix(self, series):
        """Generate a field name prefix from the series instance uid."""
        image = series.images.first()
        return f"{image.laterality}{image.view_position}".lower()

    def _get_series_fingerprint(self, series_list):
        """Generate a fingerprint representing the current series state for stale form detection."""
        data = [s.series_instance_uid for s in series_list]
        return json.dumps(data)
