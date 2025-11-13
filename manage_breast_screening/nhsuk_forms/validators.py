import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxWordValidator:
    def __init__(self, max_words):
        self.max_words = max_words

    def __call__(self, value):
        if not value:
            return

        words = re.split(r"\s+", str(value).strip())

        if len(words) > self.max_words:
            raise ValidationError(
                f"Enter {self.max_words} words or less",
                params={"value": value},
                code="max_words",
            )


@deconstructible
class ExcludesOtherOptionsValidator:
    """
    Validate ArrayFields of choices that contain an exclusive choice
    (i.e. a checkbox that excludes all the other checkboxes)
    """

    def __init__(self, option_that_excludes_other_options, option_label):
        self.option_that_excludes_other_options = option_that_excludes_other_options
        self.option_label = option_label

    def __call__(self, value):
        if not value:
            return

        if self.option_that_excludes_other_options in value and len(value) > 1:
            raise ValidationError(
                f'Unselect "{self.option_label}" in order to select other options'
            )
