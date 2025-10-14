import pytest
from django.forms import ValidationError

from .. import validators


class TestMaxWordsValidator:
    @pytest.fixture
    def validator(self):
        return validators.MaxWordValidator(3)

    def test_under_limit(self, validator):
        assert validator("one two three") is None

    def test_over_limit(self, validator):
        with pytest.raises(ValidationError, match=""):
            validator("one two three four")

    def test_ignores_whitespace_at_begining_and_end(self, validator):
        assert validator("\none two three\n") is None

    def test_counts_multiple_spaces_as_one(self, validator):
        assert validator("one\t two  \nthree") is None
