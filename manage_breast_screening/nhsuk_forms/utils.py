from .choices import YesNo
from .fields.choice_fields import ChoiceField


def yes_no_field(**kwargs) -> ChoiceField:
    return ChoiceField(choices=YesNo, **kwargs)
