from manage_breast_screening.nhsuk_forms.fields import CharField, ChoiceField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)


class HormoneReplacementTherapyForm(FormWithConditionalFields):
    def __init__(self, *args, participant, **kwargs):
        self.instance = kwargs.pop("instance", None)

        if self.instance:
            kwargs["initial"] = self.initial_values(self.instance)

        super().__init__(*args, **kwargs)

        self.fields["status"] = ChoiceField(
            choices=HormoneReplacementTherapy.Status,
            label=f"Is {participant.full_name} currently taking HRT?",
            label_classes="nhsuk-label--l",
            page_heading=True,
            error_messages={
                "required": "Select whether they are currently taking HRT or not"
            },
        )
        self.fields["approx_start_date"] = CharField(
            required=False,
            label="Approximate date started",
            hint="For example, August 2024",
            error_messages={
                "required": "Provide approximate date when they started taking HRT"
            },
            classes="nhsuk-u-width-two-thirds",
        )
        self.fields["approx_end_date"] = CharField(
            required=False,
            label="Approximate date stopped",
            hint="For example, December 2025",
            error_messages={
                "required": "Provide approximate date when they stopped taking HRT"
            },
            classes="nhsuk-u-width-two-thirds",
        )
        self.fields["approx_previous_duration"] = CharField(
            required=False,
            label="Approximate time taken for",
            hint="For example, 5 years",
            error_messages={
                "required": "Provide approximate time they were taking HRT for"
            },
            classes="nhsuk-u-width-two-thirds",
        )

        self.given_field_value(
            "status", HormoneReplacementTherapy.Status.YES
        ).require_field("approx_start_date")
        self.given_field_value(
            "status", HormoneReplacementTherapy.Status.NO_BUT_STOPPED_RECENTLY
        ).require_field("approx_end_date")
        self.given_field_value(
            "status", HormoneReplacementTherapy.Status.NO_BUT_STOPPED_RECENTLY
        ).require_field("approx_previous_duration")

    def initial_values(self, instance):
        return {
            "status": instance.status,
            "approx_start_date": instance.approx_start_date,
            "approx_end_date": instance.approx_end_date,
            "approx_previous_duration": instance.approx_previous_duration,
        }

    def create(self, appointment):
        return HormoneReplacementTherapy.objects.create(
            appointment=appointment,
            status=self.cleaned_data["status"],
            approx_start_date=self.cleaned_data.get("approx_start_date", ""),
            approx_end_date=self.cleaned_data.get("approx_end_date", ""),
            approx_previous_duration=self.cleaned_data.get(
                "approx_previous_duration", ""
            ),
        )

    def update(self):
        self.instance.status = self.cleaned_data["status"]
        self.instance.approx_start_date = self.cleaned_data.get("approx_start_date", "")
        self.instance.approx_end_date = self.cleaned_data.get("approx_end_date", "")
        self.instance.approx_previous_duration = self.cleaned_data.get(
            "approx_previous_duration", ""
        )
        self.instance.save()

        return self.instance
