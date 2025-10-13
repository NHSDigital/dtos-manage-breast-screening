from datetime import date

from django.db.models import TextChoices
from django.forms import CheckboxSelectMultiple
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    SplitDateField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    MultipleChoiceField,
    RadioSelectWithoutFieldset,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.nhsuk_forms.utils import YesNo, yes_no, yes_no_field
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    RelativeDateChoices,
    SkinChangeChoices,
    SymptomAreas,
    SymptomType,
)


class RightLeftOtherChoices(TextChoices):
    RIGHT_BREAST = SymptomAreas.RIGHT_BREAST.value, SymptomAreas.RIGHT_BREAST.label
    LEFT_BREAST = SymptomAreas.LEFT_BREAST.value, SymptomAreas.LEFT_BREAST.label
    OTHER = SymptomAreas.OTHER.value, SymptomAreas.OTHER.label


class RightLeftNippleChoices(TextChoices):
    RIGHT_BREAST = SymptomAreas.RIGHT_BREAST.value, "Right nipple"
    LEFT_BREAST = SymptomAreas.LEFT_BREAST.value, "Left nipple"


class CommonFields:
    """
    Fields that can be mixed and matched on the Form classes for specific symptom types
    """

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
        error_messages={"required": "Enter when the symptom was resolved"},
    )
    investigated = yes_no_field(
        label="Has this been investigated?",
        error_messages={
            "required": "Select whether the symptom has been investigated or not"
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
        max_words=500,
        error_messages={"max_words": "Additional details must be 500 words or less"},
    )

    @staticmethod
    def area_radios(symptom_name="symptom"):
        return ChoiceField(
            choices=RightLeftOtherChoices,
            label=f"Where is the {symptom_name} located?",
            error_messages={"required": f"Select the location of the {symptom_name}"},
        )

    @staticmethod
    def area_description(
        symptom_name="symptom",
        hint="For example, the left armpit",
        visually_hidden_label_suffix=None,
    ):
        return CharField(
            required=False,
            label="Describe the specific area",
            hint=hint,
            error_messages={
                "required": f"Describe the specific area where the {symptom_name} is located"
            },
            classes="nhsuk-u-width-two-thirds",
            visually_hidden_label_suffix=visually_hidden_label_suffix,
        )


class SymptomForm(FormWithConditionalFields):
    """
    A base form class for entering symptoms. To be overriden for different symptom types.
    """

    def __init__(self, symptom_type, instance=None, **kwargs):
        self.instance = instance
        self.symptom_type = symptom_type

        if instance:
            kwargs["initial"] = self.initial_values(instance)

        super().__init__(**kwargs)

    def initial_values(self, instance):
        """
        Map a Symptom record to initial values for the form
        """
        return {
            "area": instance.area,
            f"area_description_{instance.area.lower()}": instance.area_description,
            "symptom_sub_type": instance.symptom_sub_type_id,
            "symptom_sub_type_details": instance.symptom_sub_type_details,
            "when_started": instance.when_started,
            "specific_date": (instance.month_started, instance.year_started),
            "intermittent": instance.intermittent,
            "recently_resolved": instance.recently_resolved,
            "when_resolved": instance.when_resolved,
            "investigated": yes_no(instance.investigated),
            "investigation_details": instance.investigation_details,
            "additional_information": instance.additional_information,
        }

    def model_values(self):
        """
        Further clean the form data to match the model, including
        splitting year/month tuples into multiple fields, and blanking
        conditionally revealed fields that are no longer visible.
        """
        match self.cleaned_data["area"]:
            case [SymptomAreas.RIGHT_BREAST, SymptomAreas.LEFT_BREAST]:
                area = SymptomAreas.BOTH_BREASTS
            case [one]:
                area = one
            case _:
                area = self.cleaned_data["area"]
                area_description_field_name = f"area_description_{area.lower()}"
                area_description = self.cleaned_data.get(
                    area_description_field_name, ""
                )

        area_description_field_name = f"area_description_{area.lower()}"
        area_description = self.cleaned_data.get(area_description_field_name, "")

        symptom_sub_type = self.cleaned_data.get("symptom_sub_type")
        symptom_sub_type_details = self.cleaned_data.get("symptom_sub_type_details", "")
        when_started = self.cleaned_data.get("when_started")
        specific_date = self.cleaned_data.get("specific_date")
        investigated = self.cleaned_data.get("investigated") == YesNo.YES
        investigation_details = self.cleaned_data.get("investigation_details", "")
        intermittent = self.cleaned_data.get("intermittent", False)
        recently_resolved = self.cleaned_data.get("recently_resolved", False)
        when_resolved = self.cleaned_data.get("when_resolved", "")
        additional_information = self.cleaned_data.get("additional_information", "")

        return dict(
            area=area,
            area_description=area_description,
            symptom_sub_type_id=symptom_sub_type,
            symptom_sub_type_details=symptom_sub_type_details,
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

    def update(self, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()
        symptom = self.instance

        if symptom is None:
            raise ValueError("attempting to update but instance is None")

        for fieldname, value in field_values.items():
            setattr(symptom, fieldname, value)

        symptom.save(update_fields=field_values.keys())

        auditor.audit_update(symptom)

        return symptom

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()

        symptom = appointment.symptom_set.create(
            appointment=appointment,
            symptom_type_id=self.symptom_type,
            reported_at=date.today(),
            **field_values,
        )

        auditor.audit_create(symptom)

        return symptom


class LumpForm(SymptomForm):
    area = CommonFields.area_radios(symptom_name="lump")
    area_description_right_breast = CommonFields.area_description(
        "lump", visually_hidden_label_suffix="right breast"
    )
    area_description_left_breast = CommonFields.area_description(
        "lump", visually_hidden_label_suffix="left breast"
    )
    area_description_other = CommonFields.area_description(
        "lump", visually_hidden_label_suffix="other"
    )
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

        self.given_field("area").require_field_with_prefix("area_description")

        self.given_field_value(
            "when_started", RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        ).require_field("specific_date")

        self.given_field_value("recently_resolved", True).require_field("when_resolved")

        self.given_field_value("investigated", YesNo.YES).require_field(
            "investigation_details"
        )


class SwellingOrShapeChangeForm(SymptomForm):
    area = CommonFields.area_radios(symptom_name="swelling or shape change")
    area_description_right_breast = CommonFields.area_description(
        "swelling or shape change", visually_hidden_label_suffix="right breast"
    )
    area_description_left_breast = CommonFields.area_description(
        "swelling or shape change", visually_hidden_label_suffix="left breast"
    )
    area_description_other = CommonFields.area_description(
        "swelling or shape change", visually_hidden_label_suffix="other"
    )
    when_started = CommonFields.when_started
    specific_date = CommonFields.specific_date
    intermittent = CommonFields.intermittent
    recently_resolved = CommonFields.recently_resolved
    when_resolved = CommonFields.when_resolved
    investigated = CommonFields.investigated
    investigation_details = CommonFields.investigation_details
    additional_information = CommonFields.additional_information

    def __init__(self, instance=None, **kwargs):
        super().__init__(
            symptom_type=SymptomType.SWELLING_OR_SHAPE_CHANGE,
            instance=instance,
            **kwargs,
        )

        self.given_field("area").require_field_with_prefix("area_description")

        self.given_field_value(
            "when_started", RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        ).require_field("specific_date")

        self.given_field_value("recently_resolved", True).require_field("when_resolved")

        self.given_field_value("investigated", YesNo.YES).require_field(
            "investigation_details"
        )


class SkinChangeForm(SymptomForm):
    area = CommonFields.area_radios(symptom_name="skin change")
    area_description_right_breast = CommonFields.area_description(
        "skin change", visually_hidden_label_suffix="right breast"
    )
    area_description_left_breast = CommonFields.area_description(
        "skin change", visually_hidden_label_suffix="left breast"
    )
    area_description_other = CommonFields.area_description(
        "skin change", visually_hidden_label_suffix="other"
    )
    symptom_sub_type = ChoiceField(
        choices=SkinChangeChoices,
        label="How has the skin changed?",
        error_messages={"required": "Select how the skin has changed"},
    )
    symptom_sub_type_details = CharField(
        required=False,
        label="Describe the change",
        error_messages={"required": "Enter a description of the change"},
        classes="nhsuk-u-width-two-thirds",
    )
    when_started = CommonFields.when_started
    specific_date = CommonFields.specific_date
    intermittent = CommonFields.intermittent
    recently_resolved = CommonFields.recently_resolved
    when_resolved = CommonFields.when_resolved
    investigated = CommonFields.investigated
    investigation_details = CommonFields.investigation_details
    additional_information = CommonFields.additional_information

    def __init__(self, instance=None, **kwargs):
        super().__init__(
            symptom_type=SymptomType.SKIN_CHANGE,
            instance=instance,
            **kwargs,
        )

        self.given_field("area").require_field_with_prefix("area_description")

        self.given_field_value(
            "when_started", RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        ).require_field("specific_date")

        self.given_field_value("recently_resolved", True).require_field("when_resolved")

        self.given_field_value("investigated", YesNo.YES).require_field(
            "investigation_details"
        )

        self.given_field_value(
            "symptom_sub_type", SkinChangeChoices.OTHER
        ).require_field("symptom_sub_type_details")


class NippleChangeForm(SymptomForm):
    area = MultipleChoiceField(
        choices=RightLeftNippleChoices,
        widget=CheckboxSelectMultiple,
        label="Which nipple has changed?",
        error_messages={"required": "Select which nipples have changed"},
        classes="app-checkboxes--inline",
    )
    symptom_sub_type = ChoiceField(
        choices=NippleChangeChoices,
        label="Describe the change",
        error_messages={"required": "Describe the change"},
    )
    symptom_sub_type_details = CharField(
        required=False,
        label="Provide details",
        error_messages={"required": "Enter details of the change"},
        classes="nhsuk-u-width-two-thirds",
    )
    when_started = CommonFields.when_started
    specific_date = CommonFields.specific_date
    intermittent = CommonFields.intermittent
    recently_resolved = CommonFields.recently_resolved
    when_resolved = CommonFields.when_resolved
    investigated = CommonFields.investigated
    investigation_details = CommonFields.investigation_details
    additional_information = CommonFields.additional_information

    def __init__(self, instance=None, **kwargs):
        super().__init__(
            symptom_type=SymptomType.NIPPLE_CHANGE,
            instance=instance,
            **kwargs,
        )

        self.given_field_value(
            "when_started", RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        ).require_field("specific_date")

        self.given_field_value("recently_resolved", True).require_field("when_resolved")

        self.given_field_value("investigated", YesNo.YES).require_field(
            "investigation_details"
        )

        self.given_field_value(
            "symptom_sub_type", NippleChangeChoices.OTHER
        ).require_field("symptom_sub_type_details")

    def initial_values(self, instance):
        return {
            "area": self.area_initial(instance.area),
            "symptom_sub_type": instance.symptom_sub_type_id,
            "symptom_sub_type_details": instance.symptom_sub_type_details,
            "when_started": instance.when_started,
            "specific_date": (instance.month_started, instance.year_started),
            "intermittent": instance.intermittent,
            "recently_resolved": instance.recently_resolved,
            "when_resolved": instance.when_resolved,
            "investigated": yes_no(instance.investigated),
            "investigation_details": instance.investigation_details,
            "additional_information": instance.additional_information,
        }

    def area_initial(self, area):
        if area == SymptomAreas.BOTH_BREASTS:
            return [
                RightLeftNippleChoices.RIGHT_BREAST.value,
                RightLeftNippleChoices.LEFT_BREAST.value,
            ]
        else:
            return [area]


class OtherSymptomForm(SymptomForm):
    area = CommonFields.area_radios()
    area_description_right_breast = CommonFields.area_description(
        visually_hidden_label_suffix="right breast"
    )
    area_description_left_breast = CommonFields.area_description(
        visually_hidden_label_suffix="left breast"
    )
    area_description_other = CommonFields.area_description(
        visually_hidden_label_suffix="other"
    )
    symptom_sub_type_details = CharField(
        label="Describe the symptom",
        label_classes="nhsuk-label--m",
        error_messages={"required": "Enter a description of the symptom"},
        classes="nhsuk-u-width-two-thirds",
    )
    when_started = CommonFields.when_started
    specific_date = CommonFields.specific_date
    intermittent = CommonFields.intermittent
    recently_resolved = CommonFields.recently_resolved
    when_resolved = CommonFields.when_resolved
    investigated = CommonFields.investigated
    investigation_details = CommonFields.investigation_details
    additional_information = CommonFields.additional_information

    def __init__(self, instance=None, **kwargs):
        super().__init__(
            symptom_type=SymptomType.OTHER,
            instance=instance,
            **kwargs,
        )

        self.given_field("area").require_field_with_prefix("area_description")

        self.given_field_value(
            "when_started", RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        ).require_field("specific_date")

        self.given_field_value("recently_resolved", True).require_field("when_resolved")

        self.given_field_value("investigated", YesNo.YES).require_field(
            "investigation_details"
        )
