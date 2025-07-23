import datetime

import pytest
from django.core.exceptions import ValidationError
from django.forms import CharField, ChoiceField, Form
from pytest_django.asserts import assertHTMLEqual

from ..form_fields import ConditionalField, SplitDateField


class TestSplitDateField:
    def test_clean(self):
        f = SplitDateField(max_value=datetime.date(2026, 6, 30))

        assert f.clean([1, 12, 2025]) == datetime.date(2025, 12, 1)

        with pytest.raises(ValidationError, match="This field is required."):
            f.clean(None)

        with pytest.raises(ValidationError, match="This field is required."):
            f.clean("")

        with pytest.raises(ValidationError, match="Enter a valid date."):
            f.clean("hello")

        with pytest.raises(
            ValidationError,
            match=r"\['Enter day as a number.', 'Enter month as a number.', 'Enter year as a number.'\]",
        ):
            f.clean(["a", "b", "c"])

        with pytest.raises(
            ValidationError,
            match=r"\['This field is required.'\]",
        ):
            f.clean(["", "", ""])

        with pytest.raises(
            ValidationError,
            match=r"\['Day should be between 1 and 31.', 'Month should be between 1 and 12.', 'Year should be between 1900 and 2026.']",
        ):
            f.clean([0, 13, 1800])

        with pytest.raises(
            ValidationError,
            match=r"\['Enter a date before 30 June 2026'\]",
        ):
            f.clean([1, 7, 2026])

    def test_has_changed(self):
        f = SplitDateField(max_value=datetime.date(2026, 12, 31))
        assert f.has_changed([1, 12, 2025], [2, 12, 2025])
        assert f.has_changed([1, 12, 2025], [1, 11, 2025])
        assert f.has_changed([1, 12, 2025], [1, 12, 2026])
        assert not f.has_changed([1, 12, 2025], [1, 12, 2025])

    def test_default_django_render(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm()

        assertHTMLEqual(
            str(f),
            """<div>
            <div class="nhsuk-form-group">
                <fieldset class="nhsuk-fieldset" role="group">
                    <legend class="nhsuk-fieldset__legend nhsuk-fieldset__legend--m">
                        Date
                    </legend>
                    <div class="nhsuk-date-input">
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date">
                                Day
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-2" id="id_date" name="date_0" type="text" inputmode="numeric">
                            </div>
                        </div>
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date_1">
                                Month
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-2" id="id_date_1" name="date_1" type="text" inputmode="numeric">
                            </div>
                        </div>
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date_2">
                                Year
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-4" id="id_date_2" name="date_2" type="text" inputmode="numeric">
                            </div>
                        </div>
                    </div>
                </fieldset>
            </div></div>
            """,
        )

    def test_default_django_render_in_bound_form(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2025"})

        assertHTMLEqual(
            str(f),
            """<div>
            <div class="nhsuk-form-group">
                <fieldset class="nhsuk-fieldset" role="group">
                    <legend class="nhsuk-fieldset__legend nhsuk-fieldset__legend--m">
                        Date
                    </legend>
                    <div class="nhsuk-date-input">
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date">
                                Day
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-2" id="id_date" name="date_0" type="text" inputmode="numeric" value="1">
                            </div>
                        </div>
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date_1">
                                Month
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-2" id="id_date_1" name="date_1" type="text" inputmode="numeric" value="12">
                            </div>
                        </div>
                        <div class="nhsuk-date-input__item">
                            <div class="nhsuk-form-group">
                                <label class="nhsuk-label nhsuk-date-input__label" for="id_date_2">
                                Year
                                </label>
                                <input class="nhsuk-input nhsuk-date-input__input nhsuk-input--width-4" id="id_date_2" name="date_2" type="text" inputmode="numeric" value="2025">
                            </div>
                        </div>
                    </div>
                </fieldset>
            </div></div>
            """,
        )

    def test_form_cleaned_data(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2025"})

        assert f.is_valid()
        assert f.cleaned_data["date"] == datetime.date(2025, 12, 1)

    def test_bound_field_subwidgets(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2025"})
        field = f["date"]

        assert len(field.subwidgets) == 3

        assert field.subwidgets[0].data == {
            "attrs": {
                "id": "id_date_0",
                "max": 31,
                "min": 1,
                "required": True,
            },
            "is_hidden": False,
            "name": "date_0",
            "required": False,
            "template_name": "django/forms/widgets/number.html",
            "type": "number",
            "value": "1",
        }

        assert field.subwidgets[1].data == {
            "attrs": {
                "id": "id_date_1",
                "max": 12,
                "min": 1,
                "required": True,
            },
            "is_hidden": False,
            "name": "date_1",
            "required": False,
            "template_name": "django/forms/widgets/number.html",
            "type": "number",
            "value": "12",
        }

        assert field.subwidgets[2].data == {
            "attrs": {
                "id": "id_date_2",
                "max": 2026,
                "min": 1900,
                "required": True,
            },
            "is_hidden": False,
            "name": "date_2",
            "required": False,
            "template_name": "django/forms/widgets/number.html",
            "type": "number",
            "value": "2025",
        }

    def test_subfield_errors_on_form(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2027"})
        assert not f.is_valid()
        assert f.errors == {"date": ["Year should be between 1900 and 2026."]}

    def test_same_year_but_past_max_value(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 7, 1))

        f = TestForm({"date_0": "1", "date_1": "8", "date_2": "2026"})
        assert not f.is_valid()
        assert f.errors == {"date": ["Enter a date before 1 July 2026"]}


class TestConditionalField:
    def test_clean_with_revealed_field(self):
        field = ConditionalField(
            choice_field=ChoiceField(
                choices=(("simple", "Simple option"), ("other", "Other"))
            ),
            revealed_fields={"other": {"details": CharField()}},
        )

        assert field.clean(["other", "some details"]) == {
            "choice": "other",
            "other_details": "some details",
        }

        with pytest.raises(
            ValidationError,
            match=r"\['This field is required.'\]",
        ):
            field.clean(["", ""])

    def test_conditionally_revealed_field_is_not_required_if_unselected(self):
        field = ConditionalField(
            choice_field=ChoiceField(
                choices=(("simple", "Simple option"), ("other", "Other"))
            ),
            revealed_fields={"other": {"details": CharField()}},
        )

        assert field.clean(["simple", ""]) == {
            "choice": "simple",
            "other_details": "",
        }

    def test_conditionally_revealed_field_is_required_if_selected(self):
        field = ConditionalField(
            choice_field=ChoiceField(
                choices=(("simple", "Simple option"), ("other", "Other"))
            ),
            revealed_fields={"other": {"details": CharField()}},
        )

        with pytest.raises(
            ValidationError,
            match=r"\['This field is required.'\]",
        ):
            field.clean(["other", ""])

    def test_incomplete_values(self):
        field = ConditionalField(
            choice_field=ChoiceField(
                choices=(("simple", "Simple option"), ("other", "Other"))
            ),
            revealed_fields={"other": {"details": CharField()}},
        )

        # Required case
        with pytest.raises(
            ValidationError,
            match=r"\['This field is required.'\]",
        ):
            field.clean(["other", None])

        # Not required case
        field.clean(["simple", None])

    def test_decompress_with_revealed_field(self):
        field = ConditionalField(
            choice_field=ChoiceField(
                choices=(("simple", "Simple option"), ("other", "Other"))
            ),
            revealed_fields={"other": {"details": CharField()}},
        )

        assert field.widget.decompress({"choice": "other", "other_details": ""}) == [
            "other",
            "",
        ]

        assert field.widget.decompress(
            {"choice": "simple", "other_details": "some details"}
        ) == ["simple", "some details"]

        assert field.widget.decompress({}) == [None, None]
