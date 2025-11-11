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
        with pytest.raises(ValidationError, match=r"\['Enter 3 words or less'\]"):
            validator("one two three four")

    def test_ignores_whitespace_at_begining_and_end(self, validator):
        assert validator("\none two three\n") is None

    def test_counts_multiple_spaces_as_one(self, validator):
        assert validator("one\t two  \nthree") is None


class TestExcludesOtherOptionsValidator:
    @pytest.fixture
    def validator(self):
        return validators.ExcludesOtherOptionsValidator(
            "NONE_OF_THE_ABOVE", "None of the above"
        )

    @pytest.mark.parametrize(
        "data", [[], None, ["NONE_OF_THE_ABOVE"], ["foo", "bar", "baz"]]
    )
    def test_valid_data(self, validator, data):
        assert validator(data) is None

    def test_invalid_data(self, validator):
        with pytest.raises(
            ValidationError,
            match=r"\['Unselect \"None of the above\" in order to select other options'\]",
        ):
            validator(["foo", "bar", "baz", "NONE_OF_THE_ABOVE"])
