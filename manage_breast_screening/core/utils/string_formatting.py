import re

import phonenumbers


def sentence_case(value):
    """
    Capitalise the first letter of a sentence.

    >>> sentence_case('a quick brown fox jumps over the lazy dog')
    'A quick brown fox jumps over the lazy dog'

    Unlike the built in `capitalize` filter, this will preserve
    capital letters already in the string:

    >>> sentence_case('not in PACS')
    'Not in PACS'
    """
    if not value:
        return ""

    return value[0].upper() + value[1:]


def format_nhs_number(value):
    """
    Format an NHS number with spaces

    >>> format_nhs_number('9998887777')
    '999 888 7777'
    """
    if not value:
        return ""

    digits = re.sub(r"\s", "", value)

    return f"{digits[:3]} {digits[3:6]} {digits[6:]}"


def format_age(value: int) -> str:
    """
    Format an age in years as a string

    >>> format_age(64)
    '64 years'
    """
    return f"{value} years"


def format_phone_number(value: str) -> str:
    try:
        phone = phonenumbers.parse(value, "GB")
    except phonenumbers.NumberParseException:
        return value

    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.NATIONAL)
