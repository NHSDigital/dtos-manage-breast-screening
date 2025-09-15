from datetime import date
from enum import StrEnum

from django import forms
from django.forms import ValidationError
from django.forms.widgets import Textarea

from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
    SplitDateField,
)

from .models import Ethnicity, ParticipantReportedMammogram


class EthnicityForm(forms.Form):
    ethnic_background_choice = ChoiceField(
        choices=Ethnicity.ethnic_background_ids_with_display_names(),
        required=True,
        error_messages={"required": "Select an ethnic background"},
    )

    def __init__(self, *args, **kwargs):
        if "participant" not in kwargs:
            raise ValueError("EthnicityForm requires a participant")
        self.participant = kwargs.pop("participant")
        super().__init__(*args, **kwargs)

        # Setup details fields for non-specific ethnicities
        for ethnic_background_id in self.non_specific_ethnic_backgrounds():
            self.fields[ethnic_background_id + "_details"] = CharField(
                required=False,
                label="How do they describe their background? (optional)",
            )

        # Set initial values
        participant_ethnic_background_id = self.participant.ethnic_background_id
        self.initial["ethnic_background_choice"] = participant_ethnic_background_id
        if participant_ethnic_background_id in self.non_specific_ethnic_backgrounds():
            self.initial[participant_ethnic_background_id + "_details"] = (
                self.participant.any_other_background_details
            )

    def ethnic_backgrounds_by_category(self):
        return Ethnicity.DATA.items()

    def non_specific_ethnic_backgrounds(self):
        return Ethnicity.non_specific_ethnic_backgrounds()

    def save(self):
        ethnic_background_id = self.cleaned_data["ethnic_background_choice"]
        self.participant.ethnic_background_id = ethnic_background_id

        if ethnic_background_id in self.non_specific_ethnic_backgrounds():
            details_field = ethnic_background_id + "_details"
            self.participant.any_other_background_details = self.cleaned_data.get(
                details_field
            )
        else:
            self.participant.any_other_background_details = ""

        self.participant.save()


class ParticipantReportedMammogramForm(forms.Form):
    class WhereTaken(StrEnum):
        SAME_UNIT = "same_unit"
        UK = ParticipantReportedMammogram.LocationType.ELSEWHERE_UK.value
        OUTSIDE_UK = ParticipantReportedMammogram.LocationType.OUTSIDE_UK.value
        PREFER_NOT_TO_SAY = (
            ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY.value
        )

    class WhenTaken(StrEnum):
        EXACT = "exact"
        APPROX = "approx"
        NOT_SURE = "not_sure"

    class NameIsTheSame(StrEnum):
        YES = "yes"
        NO = "no"

    def __init__(self, participant, current_provider, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.participant = participant
        self.current_provider = current_provider
        self.where_taken_choices = {
            self.WhereTaken.SAME_UNIT: f"At {current_provider.name}",
            self.WhereTaken.UK: "Somewhere in the UK",
            self.WhereTaken.OUTSIDE_UK: "Outside the UK",
            self.WhereTaken.PREFER_NOT_TO_SAY: "Prefer not to say",
        }

        self.when_taken_choices = {
            self.WhenTaken.EXACT: "Enter an exact date",
            self.WhenTaken.APPROX: "Enter an approximate date",
            self.WhenTaken.NOT_SURE: "Not sure",
        }

        self.name_is_the_same_legend = {
            "isPageHeading": False,
        }

        self.name_is_the_same_choices = {
            self.NameIsTheSame.YES: "Yes",
            self.NameIsTheSame.NO: "No, under a different name",
        }

        # Main choice fields
        self.fields["where_taken"] = ChoiceField(
            label="Where were the breast x-rays taken?",
            label_classes="nhsuk-fieldset__legend--m",
            choices=self.where_taken_choices,
        )

        self.fields["when_taken"] = ChoiceField(
            label="When were the x-rays taken?",
            label_classes="nhsuk-fieldset__legend--m",
            choices=self.when_taken_choices,
        )

        self.fields["name_is_the_same"] = ChoiceField(
            label=f"Were they taken with the name {participant.full_name}?",
            label_classes="nhsuk-fieldset__legend--m",
            choices=self.name_is_the_same_choices,
        )

        # Conditionally shown fields
        self.fields["somewhere_in_the_uk_details"] = CharField(
            required=False,
            initial="",
            widget=Textarea(attrs={"rows": "2"}),
            label="Location",
        )

        self.fields["outside_the_uk_details"] = CharField(
            required=False,
            initial="",
            label="Location",
            widget=Textarea(attrs={"rows": "2"}),
        )

        self.fields["exact_date"] = SplitDateField(
            max_value=date.today(),
            required=False,
            hint="For example, 15 3 2025",
            label="Date of mammogram",
        )

        self.fields["approx_date"] = CharField(
            required=False,
            initial="",
            label="Enter an approximate date",
            label_classes="nhsuk-u-visually-hidden",
            hint="For example, 9 months ago",
            classes="nhsuk-u-width-two-thirds",
        )

        self.fields["different_name"] = CharField(
            required=False,
            initial="",
            label="Enter the previously used name",
            classes="nhsuk-u-width-two-thirds",
        )

        # Free form field at the end
        self.fields["additional_information"] = CharField(
            required=False,
            label="Additional information (optional)",
            label_classes="nhsuk-label--m",
            initial="",
            hint="For example, the reason for the mammograms and the outcome of the assessment",
            widget=Textarea(attrs={"rows": "2"}),
        )

        # Explicitly order the films so that the error summary order
        # matches the order fields are rendered in.
        self.order_fields(
            [
                "where_taken",
                "somewhere_in_the_uk_details",
                "outside_the_uk_details",
                "when_taken",
                "exact_date",
                "approx_date",
                "name_is_the_same",
                "different_name",
                "additional_information",
            ]
        )

    def clean(self):
        cleaned_data = super().clean()

        where_taken = cleaned_data.get("where_taken")
        when_taken = cleaned_data.get("when_taken")
        name_is_the_same = cleaned_data.get("name_is_the_same")

        if where_taken == self.WhereTaken.UK and not cleaned_data.get(
            "somewhere_in_the_uk_details"
        ):
            self.add_error(
                "somewhere_in_the_uk_details",
                ValidationError(
                    "Enter the clinic or hospital name, or any location details",
                    code="required",
                ),
            )
        elif where_taken == self.WhereTaken.OUTSIDE_UK and not cleaned_data.get(
            "outside_the_uk_details"
        ):
            self.add_error(
                "outside_the_uk_details",
                ValidationError(
                    "Enter the clinic or hospital name, or any location details",
                    code="required",
                ),
            )

        if (
            when_taken == "exact"
            and not cleaned_data.get("exact_date")
            and not self.errors.get("exact_date")
        ):
            self.add_error(
                "exact_date",
                ValidationError(
                    "Enter the date when the x-rays were taken", code="required"
                ),
            )
        elif when_taken == "approx" and not cleaned_data.get("approx_date"):
            self.add_error(
                "approx_date",
                ValidationError(
                    "Enter the approximate date when the x-rays were taken",
                    code="required",
                ),
            )

        if name_is_the_same == "no" and not cleaned_data.get("different_name"):
            self.add_error(
                "different_name",
                ValidationError(
                    "Enter the name the x-rays were taken with", code="required"
                ),
            )

    def set_location_fields(self, instance):
        where_taken = self.cleaned_data["where_taken"]

        if where_taken == self.WhereTaken.SAME_UNIT:
            instance.location_type = (
                ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT
            )
        elif where_taken == self.WhereTaken.OUTSIDE_UK:
            instance.location_type = (
                ParticipantReportedMammogram.LocationType.ELSEWHERE_UK
            )
        else:
            instance.location_type = where_taken

        if where_taken == self.WhereTaken.SAME_UNIT:
            instance.provider = self.current_provider
        if where_taken == self.WhereTaken.UK:
            instance.location_details = self.cleaned_data["somewhere_in_the_uk_details"]
        elif where_taken == self.WhereTaken.OUTSIDE_UK:
            instance.location_details = self.cleaned_data["outside_the_uk_details"]

    def save(self, commit=True):
        instance = ParticipantReportedMammogram(
            participant=self.participant,
            exact_date=self.cleaned_data["exact_date"],
            approx_date=self.cleaned_data["approx_date"],
            different_name=self.cleaned_data["different_name"],
            additional_information=self.cleaned_data["additional_information"],
        )

        self.set_location_fields(instance)

        if commit:
            instance.save()

        return instance
