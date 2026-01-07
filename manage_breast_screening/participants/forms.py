from datetime import date

from django import forms
from django.db.models import TextChoices
from django.forms.widgets import Textarea

from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
)
from manage_breast_screening.nhsuk_forms.fields.split_date_field import SplitDateField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields

from .models import AppointmentReportedMammogram, Ethnicity


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


class AppointmentReportedMammogramForm(FormWithConditionalFields):
    class WhenTaken(TextChoices):
        EXACT = (
            "EXACT",
            "Enter an exact date",
        )
        APPROX = "APPROX", "Enter an approximate date"
        NOT_SURE = "NOT_SURE", "Not sure"

    class NameIsTheSame(TextChoices):
        YES = "YES", "Yes"
        NO = "NO", "No, under a different name"

    def __init__(
        self,
        *args,
        participant,
        most_recent_provider,
        instance=None,
        **kwargs,
    ):
        self.instance = instance

        if instance:
            kwargs["initial"] = {
                "location_type": instance.location_type,
                "somewhere_in_the_uk_details": instance.location_details,
                "outside_the_uk_details": instance.location_details,
                "when_taken": (
                    self.WhenTaken.EXACT
                    if instance.exact_date
                    else self.WhenTaken.APPROX
                    if instance.approx_date
                    else self.WhenTaken.NOT_SURE
                ),
                "name_is_the_same": (
                    self.NameIsTheSame.YES
                    if not instance.different_name
                    else self.NameIsTheSame.NO
                ),
                "exact_date": instance.exact_date,
                "approx_date": instance.approx_date,
                "different_name": instance.different_name,
                "additional_information": instance.additional_information,
            }

        super().__init__(*args, **kwargs)

        self.participant = participant
        self.most_recent_provider = most_recent_provider

        location_choices = []
        for value, label in AppointmentReportedMammogram.LocationType.choices:
            if (
                value
                == AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT
            ):
                label = f"At {most_recent_provider.name}"
            elif value == AppointmentReportedMammogram.LocationType.ELSEWHERE_UK:
                label = "Somewhere in the UK"
            location_choices.append((value, label))

        self.fields["location_type"] = ChoiceField(
            choices=location_choices,
            label="Where were the breast x-rays taken?",
            error_messages={"required": "Select where the breast x-rays were taken"},
        )
        self.fields["somewhere_in_the_uk_details"] = CharField(
            required=False,
            label="Location",
            widget=Textarea(attrs={"rows": "2"}),
            error_messages={
                "required": "Enter the clinic or hospital name, or any location details"
            },
        )
        self.given_field_value(
            "location_type", AppointmentReportedMammogram.LocationType.ELSEWHERE_UK
        ).require_field("somewhere_in_the_uk_details")
        self.fields["outside_the_uk_details"] = CharField(
            required=False,
            label="Location",
            widget=Textarea(attrs={"rows": "2"}),
            error_messages={
                "required": "Enter the clinic or hospital name, or any location details"
            },
        )
        self.given_field_value(
            "location_type", AppointmentReportedMammogram.LocationType.OUTSIDE_UK
        ).require_field("outside_the_uk_details")

        self.fields["when_taken"] = ChoiceField(
            choices=self.WhenTaken,
            label="When were the x-rays taken?",
            error_messages={"required": "Select when the x-rays were taken"},
        )
        self.fields["exact_date"] = SplitDateField(
            required=False,
            max_value=date.today(),
            hint="For example, 15 3 2025",
            label="Date of mammogram",
            label_classes="nhsuk-u-visually-hidden",
            error_messages={"required": "Enter the date when the x-rays were taken"},
        )
        self.given_field_value("when_taken", self.WhenTaken.EXACT).require_field(
            "exact_date"
        )
        self.fields["approx_date"] = CharField(
            required=False,
            label="Enter an approximate date",
            label_classes="nhsuk-u-visually-hidden",
            hint="For example, 9 months ago",
            classes="nhsuk-u-width-two-thirds",
            error_messages={
                "required": "Enter the approximate date when the x-rays were taken"
            },
        )
        self.given_field_value("when_taken", self.WhenTaken.APPROX).require_field(
            "approx_date"
        )

        self.fields["name_is_the_same"] = ChoiceField(
            label=f"Were they taken with the name {participant.full_name}?",
            choices=self.NameIsTheSame,
            error_messages={
                "required": "Select if the x-rays were taken with the same name"
            },
        )
        self.fields["different_name"] = CharField(
            required=False,
            label="Enter the previously used name",
            classes="nhsuk-u-width-two-thirds",
            error_messages={"required": "Enter the name the x-rays were taken with"},
        )
        self.given_field_value("name_is_the_same", self.NameIsTheSame.NO).require_field(
            "different_name"
        )

        self.fields["additional_information"] = CharField(
            hint="For example, the reason for the mammograms and the outcome of the assessment",
            required=False,
            label="Additional information (optional)",
            label_classes="nhsuk-label--m",
            widget=Textarea(attrs={"rows": 4}),
            max_words=500,
            error_messages={
                "max_words": "Additional information must be 500 words or less"
            },
        )

    def model_values(self):
        return dict(
            exact_date=self.cleaned_data.get("exact_date"),
            approx_date=self.cleaned_data.get("approx_date"),
            different_name=self.cleaned_data.get("different_name"),
            additional_information=self.cleaned_data.get("additional_information", ""),
        )

    def set_location_fields(self, instance):
        instance.location_type = self.cleaned_data["location_type"]

        if (
            instance.location_type
            == AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT
        ):
            instance.provider = self.most_recent_provider
        else:
            instance.provider = None

        if (
            instance.location_type
            == AppointmentReportedMammogram.LocationType.ELSEWHERE_UK
        ):
            instance.location_details = self.cleaned_data["somewhere_in_the_uk_details"]
        elif (
            instance.location_type
            == AppointmentReportedMammogram.LocationType.OUTSIDE_UK
        ):
            instance.location_details = self.cleaned_data["outside_the_uk_details"]
        else:
            instance.location_details = ""

    def create(self, appointment):
        field_values = self.model_values()

        instance = AppointmentReportedMammogram(
            appointment=appointment,
            **field_values,
        )

        self.set_location_fields(instance)

        instance.save()

        self.appointment_reported_mammogram_pk = instance.pk

        return instance

    def update(self):
        if self.instance is None:
            raise ValueError("Form has no instance")

        self.set_location_fields(self.instance)
        self.instance.exact_date = self.cleaned_data.get("exact_date")
        self.instance.approx_date = self.cleaned_data.get("approx_date")
        self.instance.different_name = self.cleaned_data.get("different_name")
        self.instance.additional_information = self.cleaned_data.get(
            "additional_information", ""
        )
        self.instance.save()

        self.appointment_reported_mammogram_pk = self.instance.pk

        return self.instance
