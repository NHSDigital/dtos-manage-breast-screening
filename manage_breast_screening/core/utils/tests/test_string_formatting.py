from manage_breast_screening.core.utils.string_formatting import (
    format_phone_number,
    plural,
)


def test_phone_number_formatting():
    assert format_phone_number("01234567890") == "01234 567890"
    assert format_phone_number("07123456789") == "07123 456789"
    assert format_phone_number("+441234567890") == "01234 567890"

    # exception case - returns the original string if it can't be parsed as a phone number
    assert format_phone_number("not a phone number") == "not a phone number"


def test_plural():
    assert plural("cat", 1) == "cat"
    assert plural("cat", 2) == "cats"
    assert plural("cat", 0) == "cats"
    assert plural("mouse", count=1, plural_noun="mice") == "mouse"
    assert plural("mouse", count=2, plural_noun="mice") == "mice"
