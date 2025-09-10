from django.db.models import TextChoices
from django.forms import (  # FIXME: create our own version of BooleanField
    BooleanField,
    Form,
)
from django.forms.widgets import Textarea

from manage_breast_screening.core.form_fields import (
    CharField,
    ChoiceField,
    SplitDateField,
)
from manage_breast_screening.forms.fields import yes_no_field


# TODO: delegate values to model changes
class RightLeftOtherChoices(TextChoices):
    RIGHT = "RIGHT", "Right breast"
    LEFT = "LEFT", "Left breast"
    OTHER = "OTHER", "Other"


class HowLongChoices(TextChoices):
    LESS_THAN_THREE_MONTHS = "LESS_THAN_THREE_MONTHS", "Less than 3 months"
    THREE_MONTHS_TO_A_YEAR = "THREE MONTHS TO A YEAR", "3 months to a year"
    ONE_TO_THREE_YEARS = "ONE_TO_THREE_YEARS", "1 to 3 years"
    OVER_THREE_YEARS = "OVER_THREE_YEARS", "Over 3 years"
    SINCE_A_SPECIFIC_DATE = "SINCE_A_SPECIFIC_DATE", "Since a specific date"
    NOT_SURE = "NOT_SURE", "Not sure"


# TODO: create mixin for conditional field validation


class LumpForm(Form):
    where_located = ChoiceField(
        choices=RightLeftOtherChoices,
        label="Where is the lump located?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    other_area_description = CharField(
        required=False,
        label="Describe the specific area",
        label_classes="nhsuk-fieldset__legend--m",
        hint="For example, the left armpit",
    )
    how_long = ChoiceField(
        choices=HowLongChoices,
        label="How long has this symptom existed?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    specific_date = SplitDateField(
        hint="For example, 3 2025",
        label="Date symptom started",
        label_classes="nhsuk-u-visually-hidden",
        required=False,
        include_day=False,
    )
    intermittent = BooleanField(required=False, label="The symptom is intermittent")
    recently_resolved = BooleanField(
        required=False, label="The symptom has recently resolved"
    )
    when_resolved = CharField(
        required=False, label="Describe when", hint="For example, 3 days ago"
    )
    investigated = yes_no_field(
        label="Has this been investigated?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    additional_info = CharField(
        required=False,
        label="Additional info (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
    )

    def __init__(self, instance=None, **kwargs):
        self.instance = instance
        super().__init__(**kwargs)
