import re

from django.core.exceptions import ValidationError


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
