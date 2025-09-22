from .choices import YesNo
from .fields.choice_fields import ChoiceField


def yes_no_field(**kwargs) -> ChoiceField:
    return ChoiceField(choices=YesNo, **kwargs)


def yes_no(bool):
    if bool:
        return YesNo.YES
    else:
        return YesNo.NO
