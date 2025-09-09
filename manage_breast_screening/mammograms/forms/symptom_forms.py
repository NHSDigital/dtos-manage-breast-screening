from django.db.models import TextChoices
from django.forms import (  # FIXME: create our own version of BooleanField
    BooleanField,
    Form,
)

from manage_breast_screening.core.form_fields import (
    CharField,
    ChoiceField,
    SplitDateField,
)


# TODO: delegate values to model changes
class RightOrLeftChoices(TextChoices):
    RIGHT = "RIGHT", "Right breast"
    LEFT = "LEFT", "Left breast"
    OTHER = "OTHER", "Other"


# TODO: create mixin for conditional field validation


class LumpForm(Form):
    where_located = ChoiceField(choices=RightOrLeftChoices)
    other_area_description = CharField(required=False)
    how_long = ChoiceField()
    specific_date = SplitDateField()  # TODO rebase and pick up the include_day param
    intermittent = BooleanField(required=False)
    recently_resolved = BooleanField(required=False)
    when_resolved = CharField(required=False)
    investigated = ChoiceField()
    additional_info = CharField(required=False)

    def __init__(self, instance=None):
        pass


class SwellingForm(Form):
    where_located = ChoiceField(choices=RightOrLeftChoices)
    how_long = ChoiceField()
    intermittent = BooleanField(required=False)
    recently_resolved = BooleanField(required=False)
    investigated = ChoiceField()
    additional_info = CharField(required=False)

    def __init__(self, instance=None):
        pass
