import datetime
from urllib.parse import urlencode

import pytest
from django.forms import CharField, ChoiceField, IntegerField
from django.http import QueryDict

from manage_breast_screening.nhsuk_forms.fields.split_date_field import SplitDateField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields


class TestFormWithConditionalFields:
    def test_does_nothing_if_no_fields_declared(self):
        class MyForm(FormWithConditionalFields):
            foo = CharField()

        form = MyForm({"foo": "bar"})
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "bar"

    @pytest.fixture
    def FormWithSimpleConditional(self):
        class MyForm(FormWithConditionalFields):
            foo = ChoiceField(choices=(("a", "a"), ("b", "b")))
            bar = CharField()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.given_field_value("foo", "a").require_field("bar")

        return MyForm

    @pytest.fixture
    def FormWithConditionalFieldsPerValue(self):
        class MyForm(FormWithConditionalFields):
            foo = ChoiceField(choices=(("a", "a"), ("b", "b")))
            other_a = CharField()
            other_b = CharField()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.given_field("foo").require_field_with_prefix("other")

        return MyForm

    @pytest.fixture
    def FormWithSimpleConditionalIntegerField(self):
        class MyForm(FormWithConditionalFields):
            foo = ChoiceField(choices=(("a", "a"), ("b", "b")))
            bar = IntegerField()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.given_field_value("foo", "a").require_field("bar")

        return MyForm

    @pytest.fixture
    def FormWithSimpleConditionalMultiWidget(self):
        class MyForm(FormWithConditionalFields):
            foo = ChoiceField(choices=(("a", "a"), ("b", "b")))
            bar = SplitDateField(
                max_value=datetime.date(2026, 6, 30), include_day=False
            )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.given_field_value("foo", "a").require_field("bar")

        return MyForm

    def test_simple_conditional_condition_not_met(self, FormWithSimpleConditional):
        form = FormWithSimpleConditional({"foo": "b"})
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"

    def test_simple_conditional_condition_met_valid_integer_field_not_required(
        self, FormWithSimpleConditionalIntegerField
    ):
        # value of bar is invalid, as not an integer, and not required as foo is "b", not "a"
        form = FormWithSimpleConditionalIntegerField(
            QueryDict(urlencode({"foo": "b", "bar": "42"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert form.cleaned_data["bar"] is None
        assert not form.data._mutable

    def test_simple_conditional_condition_met_invalid_integer_field_not_required(
        self, FormWithSimpleConditionalIntegerField
    ):
        # value of bar is invalid, as not an integer, and not required as foo is "b", not "a"
        form = FormWithSimpleConditionalIntegerField(
            QueryDict(urlencode({"foo": "b", "bar": "abc"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert form.cleaned_data["bar"] is None
        assert not form.data._mutable

    def test_simple_conditional_condition_met_integer_field_required(
        self, FormWithSimpleConditionalIntegerField
    ):
        # value of bar is a valid integer and is required as foo is "a"
        form = FormWithSimpleConditionalIntegerField(
            QueryDict(urlencode({"foo": "a", "bar": "42"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "a"
        assert form.cleaned_data["bar"] == 42
        assert not form.data._mutable

    def test_simple_conditional_condition_met_with_valid_date_field_not_required(
        self, FormWithSimpleConditionalMultiWidget
    ):
        # value of bar is invalid, as not a valid date, and not required as foo is "b", not "a"
        form = FormWithSimpleConditionalMultiWidget(
            QueryDict(urlencode({"foo": "b", "bar_0": "11", "bar_1": "2025"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert form.cleaned_data["bar"] is None
        assert "bar_0" not in form.data
        assert "bar_1" not in form.data
        assert not form.data._mutable

    def test_simple_conditional_condition_met_with_invalid_date_field_not_required(
        self, FormWithSimpleConditionalMultiWidget
    ):
        # value of bar is invalid, as not a valid date, and not required as foo is "b", not "a"
        form = FormWithSimpleConditionalMultiWidget(
            QueryDict(urlencode({"foo": "b", "bar_0": "99", "bar_1": "9999"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert form.cleaned_data["bar"] is None
        assert "bar_0" not in form.data
        assert "bar_1" not in form.data
        assert not form.data._mutable

    def test_simple_conditional_condition_met_with_date_field_required(
        self, FormWithSimpleConditionalMultiWidget
    ):
        # value of bar is a valid date and is required as foo is "a"
        form = FormWithSimpleConditionalMultiWidget(
            QueryDict(urlencode({"foo": "a", "bar_0": "11", "bar_1": "2025"}))
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "a"
        assert form.cleaned_data["bar"] == datetime.date(2025, 11, 1)
        assert form.data["bar_0"] == "11"
        assert form.data["bar_1"] == "2025"
        assert not form.data._mutable

    def test_simple_conditional_condition_met(self, FormWithSimpleConditional):
        form = FormWithSimpleConditional({"foo": "a", "bar": "abc"})
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "a"
        assert form.cleaned_data["bar"] == "abc"

    def test_simple_conditional_condition_missing_value(
        self, FormWithSimpleConditional
    ):
        form = FormWithSimpleConditional({"foo": "a"})
        assert not form.is_valid()
        assert form.errors == {"bar": ["This field is required."]}

    def test_simple_conditional_with_unused_value(self, FormWithSimpleConditional):
        form = FormWithSimpleConditional({"foo": "b", "bar": "abc"})
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert not form.cleaned_data.get("bar")

    def test_simple_conditional_predicate_missing(self, FormWithSimpleConditional):
        form = FormWithSimpleConditional({})
        assert not form.is_valid()
        assert form.errors == {"foo": ["This field is required."]}

    def test_per_value_conditional_missing_value(
        self, FormWithConditionalFieldsPerValue
    ):
        form = FormWithConditionalFieldsPerValue({"foo": "b"})
        assert not form.is_valid()
        assert form.errors == {"other_b": ["This field is required."]}

    def test_per_value_conditional_provided_value(
        self, FormWithConditionalFieldsPerValue
    ):
        form = FormWithConditionalFieldsPerValue({"foo": "a", "other_a": "abc"})
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "a"
        assert form.cleaned_data["other_a"] == "abc"

    def test_per_value_conditional_with_unused_value(
        self, FormWithConditionalFieldsPerValue
    ):
        form = FormWithConditionalFieldsPerValue(
            {"foo": "b", "other_a": "abc", "other_b": "def"}
        )
        assert form.is_valid()
        assert form.cleaned_data["foo"] == "b"
        assert form.cleaned_data["other_b"] == "def"
        assert not form.cleaned_data.get("other_a")

    def test_per_value_predicate_missing(self, FormWithConditionalFieldsPerValue):
        form = FormWithConditionalFieldsPerValue({})
        assert not form.is_valid()
        assert form.errors == {"foo": ["This field is required."]}
