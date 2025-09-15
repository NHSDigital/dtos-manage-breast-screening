from manage_breast_screening.core.form_fields import ChoiceField

from .choices import YesNo


def yes_no_field(**kwargs) -> ChoiceField:
    return ChoiceField(choices=YesNo, **kwargs)
