from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import TextChoices
from django.forms.widgets import Textarea

from manage_breast_screening.core.utils.date_formatting import (
    format_relative_months,
    format_relative_seasons,
)
from manage_breast_screening.nhsuk_forms.fields import CharField, ChoiceField
from manage_breast_screening.nhsuk_forms.fields.split_date_field import SplitDateField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models import ParticipantReportedMammogram


class ParticipantReportedMammogramForm(FormWithConditionalFields):
    class NameIsTheSame(TextChoices):
        YES = "YES", "Yes"
        NO = "NO", "No, under a different name"

    def __init__(
        self,
        *args,
        appointment,
        instance=None,
        **kwargs,
    ):
        self.instance = instance

        participant = appointment.screening_episode.participant
        current_provider = appointment.provider

        if instance:
            kwargs["initial"] = {
                "location_type": instance.location_type,
                "somewhere_in_the_uk_details": instance.location_details,
                "outside_the_uk_details": instance.location_details,
                "date_type": instance.date_type,
                "name_is_the_same": (
                    self.NameIsTheSame.YES
                    if not instance.different_name
                    else self.NameIsTheSame.NO
                ),
                "exact_date": instance.exact_date,
                f"approx_date_{instance.date_type}": instance.approx_date,
                "different_name": instance.different_name,
                "additional_information": instance.additional_information,
            }

        super().__init__(*args, **kwargs)

        location_choices = []
        for value, label in ParticipantReportedMammogram.LocationType.choices:
            if value == ParticipantReportedMammogram.LocationType.SAME_PROVIDER:
                label = f"At {current_provider.name}"
            elif value == ParticipantReportedMammogram.LocationType.ELSEWHERE_UK:
                label = "Somewhere in the UK"
            location_choices.append((value, label))

        self.fields["location_type"] = ChoiceField(
            choices=location_choices,
            label="Where were the breast x-rays taken?",
            error_messages={"required": "Select where the breast x-rays were taken"},
        )

        self.fields["another_nhs_provider_details"] = CharField(
            required=False,
            label="Enter the unit",
            error_messages={"required": "Enter the breast screening unit"},
        )
        self.given_field_value(
            "location_type",
            ParticipantReportedMammogram.LocationType.ANOTHER_NHS_PROVIDER,
        ).require_field("another_nhs_provider_details")

        self.fields["somewhere_in_the_uk_details"] = CharField(
            required=False,
            label="Location",
            widget=Textarea(attrs={"rows": "2"}),
            error_messages={
                "required": "Enter the clinic or hospital name, or any location details"
            },
        )
        self.given_field_value(
            "location_type", ParticipantReportedMammogram.LocationType.ELSEWHERE_UK
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
            "location_type", ParticipantReportedMammogram.LocationType.OUTSIDE_UK
        ).require_field("outside_the_uk_details")

        self.fields["date_type"] = ChoiceField(
            choices=ParticipantReportedMammogram.DateType,
            label="When were the x-rays taken?",
            error_messages={"required": "Select when the x-rays were taken"},
        )

        example_date = date.today() - relativedelta(months=9)
        self.fields["exact_date"] = SplitDateField(
            required=False,
            max_value=date.today(),
            hint=f"For example, {example_date.day} {example_date.month} {example_date.year}",
            label="Date of mammogram",
            label_classes="nhsuk-u-visually-hidden",
            error_messages={"required": "Enter the date when the x-rays were taken"},
        )
        self.given_field_value(
            "date_type", ParticipantReportedMammogram.DateType.EXACT
        ).require_field("exact_date")
        self.fields["approx_date_MORE_THAN_SIX_MONTHS"] = CharField(
            required=False,
            label="Approximate date",
            visually_hidden_label_suffix=" (at least 6 months ago)",
            hint=f"For example, {format_relative_months(-12)} or {format_relative_seasons(-4)}",
            classes="nhsuk-u-width-two-thirds",
            error_messages={
                "required": "Enter the approximate date when the x-rays were taken"
            },
        )
        self.fields["approx_date_LESS_THAN_SIX_MONTHS"] = CharField(
            required=False,
            label="Approximate date",
            visually_hidden_label_suffix=" (less than 6 months ago)",
            hint=f"For example, {format_relative_months(-3)} or {format_relative_seasons(-1)}",
            classes="nhsuk-u-width-two-thirds",
            error_messages={
                "required": "Enter the approximate date when the x-rays were taken"
            },
        )
        self.given_field_value(
            "date_type", ParticipantReportedMammogram.DateType.MORE_THAN_SIX_MONTHS
        ).require_field("approx_date_MORE_THAN_SIX_MONTHS")
        self.given_field_value(
            "date_type", ParticipantReportedMammogram.DateType.LESS_THAN_SIX_MONTHS
        ).require_field("approx_date_LESS_THAN_SIX_MONTHS")

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
        date_type = self.cleaned_data["date_type"]

        return dict(
            date_type=date_type,
            exact_date=self.cleaned_data.get("exact_date"),
            approx_date=self.cleaned_data.get(f"approx_date_{date_type}", ""),
            different_name=self.cleaned_data.get("different_name"),
            additional_information=self.cleaned_data.get("additional_information", ""),
        )

    def set_location_fields(self, instance):
        instance.location_type = self.cleaned_data["location_type"]

        if (
            instance.location_type
            == ParticipantReportedMammogram.LocationType.ANOTHER_NHS_PROVIDER
        ):
            instance.location_details = self.cleaned_data[
                "another_nhs_provider_details"
            ]
        elif (
            instance.location_type
            == ParticipantReportedMammogram.LocationType.ELSEWHERE_UK
        ):
            instance.location_details = self.cleaned_data["somewhere_in_the_uk_details"]
        elif (
            instance.location_type
            == ParticipantReportedMammogram.LocationType.OUTSIDE_UK
        ):
            instance.location_details = self.cleaned_data["outside_the_uk_details"]
        else:
            instance.location_details = ""

    def create(self, appointment):
        field_values = self.model_values()

        instance = ParticipantReportedMammogram(
            appointment=appointment,
            **field_values,
        )

        self.set_location_fields(instance)

        instance.save()

        self.participant_reported_mammogram_pk = instance.pk

        return instance

    def update(self):
        if self.instance is None:
            raise ValueError("Form has no instance")

        date_type = self.cleaned_data["date_type"]

        self.set_location_fields(self.instance)
        self.instance.date_type = date_type
        self.instance.exact_date = self.cleaned_data.get("exact_date")
        self.instance.approx_date = self.cleaned_data.get(
            f"approx_date_{date_type}", ""
        )

        self.instance.different_name = self.cleaned_data.get("different_name")
        self.instance.additional_information = self.cleaned_data.get(
            "additional_information", ""
        )
        self.instance.save()

        self.participant_reported_mammogram_pk = self.instance.pk

        return self.instance
