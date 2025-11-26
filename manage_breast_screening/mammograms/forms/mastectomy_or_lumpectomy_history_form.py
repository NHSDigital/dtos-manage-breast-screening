from django.forms import widgets
from django.forms.widgets import RadioSelect, Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
    YearField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)


class MastectomyOrLumpectomyHistoryBaseForm(FormWithConditionalFields):
    right_breast_procedure = ChoiceField(
        label="Right breast",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        widget=RadioSelect,
        choices=MastectomyOrLumpectomyHistoryItem.Procedure,
        error_messages={
            "required": "Select which procedure they have had in the right breast",
        },
    )
    left_breast_procedure = ChoiceField(
        label="Left breast",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        widget=RadioSelect,
        choices=MastectomyOrLumpectomyHistoryItem.Procedure,
        error_messages={
            "required": "Select which procedure they have had in the left breast",
        },
    )
    right_breast_other_surgery = MultipleChoiceField(
        label="Right breast",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=MastectomyOrLumpectomyHistoryItem.Surgery,
        error_messages={
            "required": "Select any other surgery they have had in the right breast",
        },
        exclusive_choices={"NO_OTHER_SURGERY"},
    )
    left_breast_other_surgery = MultipleChoiceField(
        label="Left breast",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=MastectomyOrLumpectomyHistoryItem.Surgery,
        error_messages={
            "required": "Select any other surgery they have had in the left breast",
        },
        exclusive_choices={"NO_OTHER_SURGERY"},
    )
    year_of_surgery = YearField(
        hint="Leave blank if unknown",
        required=False,
        label="Year of surgery (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
    )
    surgery_reason = ChoiceField(
        choices=MastectomyOrLumpectomyHistoryItem.SurgeryReason,
        label="Why was this surgery done?",
        widget=widgets.RadioSelect,
        error_messages={"required": "Select the reason for surgery"},
    )
    surgery_other_reason_details = CharField(
        required=False,
        label="Provide details",
        error_messages={"required": "Provide details of the surgery"},
        classes="nhsuk-u-width-two-thirds",
    )
    additional_details = CharField(
        hint="Include any other relevant information about the surgery",
        required=False,
        label="Additional details (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
        max_words=500,
        error_messages={"max_words": "Additional details must be 500 words or less"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.given_field_value(
            "surgery_reason",
            MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON,
        ).require_field("surgery_other_reason_details")

    def model_values(self):
        return dict(
            left_breast_procedure=self.cleaned_data.get("left_breast_procedure", None),
            right_breast_procedure=self.cleaned_data.get(
                "right_breast_procedure", None
            ),
            left_breast_other_surgery=self.cleaned_data.get(
                "left_breast_other_surgery", []
            ),
            right_breast_other_surgery=self.cleaned_data.get(
                "right_breast_other_surgery", []
            ),
            year_of_surgery=self.cleaned_data.get("year_of_surgery", None),
            surgery_reason=self.cleaned_data.get("surgery_reason", None),
            surgery_other_reason_details=self.cleaned_data.get(
                "surgery_other_reason_details", ""
            ),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )


class MastectomyOrLumpectomyHistoryForm(MastectomyOrLumpectomyHistoryBaseForm):
    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()

        mastectomy_or_lumpectomy_history = (
            appointment.mastectomy_or_lumpectomy_history_items.create(
                appointment=appointment,
                **field_values,
            )
        )

        auditor.audit_create(mastectomy_or_lumpectomy_history)

        return mastectomy_or_lumpectomy_history


class MastectomyOrLumpectomyHistoryUpdateForm(MastectomyOrLumpectomyHistoryBaseForm):
    def __init__(self, instance, *args, **kwargs):
        self.instance = instance

        kwargs["initial"] = {
            "left_breast_procedure": instance.left_breast_procedure,
            "right_breast_procedure": instance.right_breast_procedure,
            "left_breast_other_surgery": instance.left_breast_other_surgery,
            "right_breast_other_surgery": instance.right_breast_other_surgery,
            "year_of_surgery": instance.year_of_surgery,
            "surgery_reason": instance.surgery_reason,
            "surgery_other_reason_details": instance.surgery_other_reason_details,
            "additional_details": instance.additional_details,
        }

        super().__init__(*args, **kwargs)

    def update(self, request):
        self.instance.left_breast_procedure = self.cleaned_data["left_breast_procedure"]
        self.instance.right_breast_procedure = self.cleaned_data[
            "right_breast_procedure"
        ]
        self.instance.left_breast_other_surgery = self.cleaned_data[
            "left_breast_other_surgery"
        ]
        self.instance.right_breast_other_surgery = self.cleaned_data[
            "right_breast_other_surgery"
        ]
        self.instance.year_of_surgery = self.cleaned_data["year_of_surgery"]
        self.instance.surgery_reason = self.cleaned_data["surgery_reason"]
        self.instance.surgery_other_reason_details = self.cleaned_data[
            "surgery_other_reason_details"
        ]
        self.instance.additional_details = self.cleaned_data["additional_details"]
        self.instance.save()

        Auditor.from_request(request).audit_update(self.instance)

        return self.instance
