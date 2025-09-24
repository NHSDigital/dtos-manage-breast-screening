from dataclasses import dataclass
from datetime import date
from typing import Any

from django.db.models import TextChoices
from django.forms import Form, ValidationError
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    SplitDateField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    RadioSelectWithoutFieldset,
)
from manage_breast_screening.nhsuk_forms.utils import YesNo, yes_no_field
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomAreas,
    SymptomType,
)


class RightLeftOtherChoices(TextChoices):
    RIGHT_BREAST = SymptomAreas.RIGHT_BREAST.value, SymptomAreas.RIGHT_BREAST.label
    LEFT_BREAST = SymptomAreas.LEFT_BREAST.value, SymptomAreas.LEFT_BREAST.label
    OTHER = SymptomAreas.OTHER.value, SymptomAreas.OTHER.label


class CommonFields:
    """
    Fields that can be mixed and matched on the Form classes for specific symptom types
    """

    area = ChoiceField(
        choices=RightLeftOtherChoices,
        label="Where is the lump located?",
        error_messages={"required": "Select the location of the lump"},
    )
    area_description = CharField(
        required=False,
        label="Describe the specific area",
        hint="For example, the left armpit",
        error_messages={
            "required": "Describe the specific area where the lump is located"
        },
        classes="nhsuk-u-width-two-thirds",
    )
    when_started = ChoiceField(
        choices=RelativeDateChoices,
        label="How long has this symptom existed?",
        widget=RadioSelectWithoutFieldset,
        error_messages={"required": "Select how long the symptom has existed"},
    )
    specific_date = SplitDateField(
        hint="For example, 3 2025",
        label="Date symptom started",
        label_classes="nhsuk-u-visually-hidden",
        required=False,
        include_day=False,
        error_messages={"required": "Enter the date the symptom started"},
    )
    intermittent = BooleanField(required=False, label="The symptom is intermittent")
    recently_resolved = BooleanField(
        required=False, label="The symptom has recently resolved"
    )
    when_resolved = CharField(
        required=False,
        label="Describe when",
        hint="For example, 3 days ago",
        classes="nhsuk-u-width-two-thirds",
    )
    investigated = yes_no_field(
        label="Has this been investigated?",
        error_messages={
            "required": "Select whether the lump has been investigated or not"
        },
    )
    investigation_details = CharField(
        required=False,
        label="Provide details",
        hint="Include where, when and the outcome",
        error_messages={"required": "Enter details of any investigations"},
        classes="nhsuk-u-width-two-thirds",
    )
    additional_information = CharField(
        required=False,
        label="Additional info (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
    )


class SymptomForm(Form):
    """
    A base form class for entering symptoms. To be overriden for different symptom types.
    """

    @dataclass
    class ConditionalRequirement:
        conditionally_required_field: str
        predicate_field: str
        predicate_field_value: Any

    def __init__(self, symptom_type, instance=None, **kwargs):
        self.instance = instance
        self.symptom_type = symptom_type
        self.conditional_requirements = []
        super().__init__(**kwargs)

    def set_conditionally_required(
        self, conditionally_required_field, predicate_field, predicate_field_value
    ):
        """
        Mark a field as conditionally required if and only if another field (the predicate field)
        is set to a specific value.

        If the predicate field is set to the predicate value, this field will require a value.
        If the predicate field is set to a different value, this field's value will be ignored.
        """
        if conditionally_required_field not in self.fields:
            raise ValueError(f"{conditionally_required_field} is not a valid field")
        if predicate_field not in self.fields:
            raise ValueError(f"{predicate_field} is not a valid field")

        self.conditional_requirements.append(
            self.ConditionalRequirement(
                conditionally_required_field=conditionally_required_field,
                predicate_field=predicate_field,
                predicate_field_value=predicate_field_value,
            )
        )

        self.fields[conditionally_required_field].required = False

    def clean(self):
        for requirement in self.conditional_requirements:
            field = requirement.conditionally_required_field

            if (
                self.cleaned_data.get(requirement.predicate_field)
                == requirement.predicate_field_value
            ):
                cleaned_value = self.cleaned_data.get(field)
                if isinstance(cleaned_value, str):
                    cleaned_value = cleaned_value.strip()

                if not cleaned_value:
                    self.add_error(
                        field,
                        ValidationError(
                            message=self.fields[field].error_messages["required"],
                            code="required",
                        ),
                    )
            else:
                del self.cleaned_data[field]

    def save(self, appointment, request):
        auditor = Auditor.from_request(request)

        area = self.cleaned_data["area"]
        area_description = self.cleaned_data.get("area_description", "")
        when_started = self.cleaned_data.get("when_started")
        specific_date = self.cleaned_data.get("specific_date")
        investigated = self.cleaned_data.get("investigated") == YesNo.YES
        investigation_details = self.cleaned_data.get("investigation_details", "")
        intermittent = self.cleaned_data.get("intermittent", False)
        recently_resolved = self.cleaned_data.get("recently_resolved", False)
        when_resolved = self.cleaned_data.get("when_resolved")
        additional_information = self.cleaned_data.get("additional_information", "")

        symptom = appointment.symptom_set.create(
            appointment=appointment,
            symptom_type_id=self.symptom_type,
            reported_at=date.today(),
            area=area,
            area_description=area_description,
            investigated=investigated,
            investigation_details=investigation_details,
            when_started=when_started,
            year_started=specific_date.year if specific_date else None,
            month_started=specific_date.month if specific_date else None,
            intermittent=intermittent,
            recently_resolved=recently_resolved,
            when_resolved=when_resolved,
            additional_information=additional_information,
        )

        auditor.audit_create(symptom)

        return symptom


class LumpForm(SymptomForm):
    area = CommonFields.area
    area_description = CommonFields.area_description
    when_started = CommonFields.when_started
    specific_date = CommonFields.specific_date
    intermittent = CommonFields.intermittent
    recently_resolved = CommonFields.recently_resolved
    when_resolved = CommonFields.when_resolved
    investigated = CommonFields.investigated
    investigation_details = CommonFields.investigation_details
    additional_information = CommonFields.additional_information

    def __init__(self, instance=None, **kwargs):
        super().__init__(symptom_type=SymptomType.LUMP, instance=instance, **kwargs)

        self.set_conditionally_required(
            conditionally_required_field="area_description",
            predicate_field="area",
            predicate_field_value=RightLeftOtherChoices.OTHER,
        )
        self.set_conditionally_required(
            conditionally_required_field="specific_date",
            predicate_field="when_started",
            predicate_field_value=RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
        )
        self.set_conditionally_required(
            conditionally_required_field="investigation_details",
            predicate_field="investigated",
            predicate_field_value=YesNo.YES,
        )
