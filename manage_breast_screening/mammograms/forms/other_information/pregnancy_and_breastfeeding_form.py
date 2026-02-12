from manage_breast_screening.nhsuk_forms.fields import CharField, ChoiceField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.other_information.pregnancy_and_breastfeeding import (
    PregnancyAndBreastfeeding,
)


class PregnancyAndBreastfeedingForm(FormWithConditionalFields):
    def __init__(self, *args, participant, **kwargs):
        self.instance = kwargs.pop("instance", None)

        if self.instance:
            kwargs["initial"] = self.initial_values(self.instance)

        super().__init__(*args, **kwargs)

        self.fields["pregnancy_status"] = ChoiceField(
            choices=PregnancyAndBreastfeeding.PregnancyStatus,
            label=f"Is {participant.full_name} pregnant?",
            error_messages={
                "required": "Select whether they are currently pregnant or not"
            },
        )
        self.fields["approx_pregnancy_due_date"] = CharField(
            required=False,
            label="Approximate due date",
            hint="For example, May 2026",
            error_messages={"required": "Provide approximate due date"},
            classes="nhsuk-u-width-two-thirds",
        )
        self.fields["approx_pregnancy_end_date"] = CharField(
            required=False,
            label="Approximate date pregnancy ended",
            hint="For example, December 2025",
            error_messages={"required": "Provide approximate date pregnancy ended"},
            classes="nhsuk-u-width-two-thirds",
        )
        self.given_field_value(
            "pregnancy_status", PregnancyAndBreastfeeding.PregnancyStatus.YES
        ).require_field("approx_pregnancy_due_date")
        self.given_field_value(
            "pregnancy_status",
            PregnancyAndBreastfeeding.PregnancyStatus.NO_BUT_HAS_BEEN_RECENTLY,
        ).require_field("approx_pregnancy_end_date")

        self.fields["breastfeeding_status"] = ChoiceField(
            choices=PregnancyAndBreastfeeding.BreastfeedingStatus,
            label="Are they currently breastfeeding?",
            error_messages={
                "required": "Select whether they are currently breastfeeding or not"
            },
        )
        self.fields["approx_breastfeeding_start_date"] = CharField(
            required=False,
            label="Approximate date started",
            hint="For example, since December 2025",
            error_messages={
                "required": "Provide details of when they started breastfeeding"
            },
            classes="nhsuk-u-width-two-thirds",
        )
        self.fields["approx_breastfeeding_end_date"] = CharField(
            required=False,
            label="Approximate date stopped",
            hint="For example, November 2025",
            error_messages={
                "required": "Provide details of when they stopped breastfeeding"
            },
            classes="nhsuk-u-width-two-thirds",
        )
        self.given_field_value(
            "breastfeeding_status", PregnancyAndBreastfeeding.BreastfeedingStatus.YES
        ).require_field("approx_breastfeeding_start_date")
        self.given_field_value(
            "breastfeeding_status",
            PregnancyAndBreastfeeding.BreastfeedingStatus.NO_BUT_STOPPED_RECENTLY,
        ).require_field("approx_breastfeeding_end_date")

    def initial_values(self, instance):
        return {
            "pregnancy_status": instance.pregnancy_status,
            "approx_pregnancy_due_date": instance.approx_pregnancy_due_date,
            "approx_pregnancy_end_date": instance.approx_pregnancy_end_date,
            "breastfeeding_status": instance.breastfeeding_status,
            "approx_breastfeeding_start_date": instance.approx_breastfeeding_start_date,
            "approx_breastfeeding_end_date": instance.approx_breastfeeding_end_date,
        }

    def create(self, appointment):
        return PregnancyAndBreastfeeding.objects.create(
            appointment=appointment,
            pregnancy_status=self.cleaned_data["pregnancy_status"],
            approx_pregnancy_due_date=self.cleaned_data.get(
                "approx_pregnancy_due_date", ""
            ),
            approx_pregnancy_end_date=self.cleaned_data.get(
                "approx_pregnancy_end_date", ""
            ),
            breastfeeding_status=self.cleaned_data.get("breastfeeding_status", ""),
            approx_breastfeeding_start_date=self.cleaned_data.get(
                "approx_breastfeeding_start_date", ""
            ),
            approx_breastfeeding_end_date=self.cleaned_data.get(
                "approx_breastfeeding_end_date", ""
            ),
        )

    def update(self):
        self.instance.pregnancy_status = self.cleaned_data["pregnancy_status"]
        self.instance.approx_pregnancy_due_date = self.cleaned_data.get(
            "approx_pregnancy_due_date", ""
        )
        self.instance.approx_pregnancy_end_date = self.cleaned_data.get(
            "approx_pregnancy_end_date", ""
        )
        self.instance.breastfeeding_status = self.cleaned_data["breastfeeding_status"]
        self.instance.approx_breastfeeding_start_date = self.cleaned_data.get(
            "approx_breastfeeding_start_date", ""
        )
        self.instance.approx_breastfeeding_end_date = self.cleaned_data.get(
            "approx_breastfeeding_end_date", ""
        )
        self.instance.save()

        return self.instance
