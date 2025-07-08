import datetime

import pytest
from django.core.exceptions import ValidationError
from django.forms import Form
from pytest_django.asserts import assertHTMLEqual

from ..form_fields import SplitDateField


class TestSplitDateField:
    def test_clean(self):
        f = SplitDateField(max_value=datetime.date(2026, 12, 31))

        assert f.clean([1, 12, 2025]) == datetime.date(2025, 12, 1)

        with pytest.raises(ValidationError, match="This field is required."):
            f.clean(None)

        with pytest.raises(ValidationError, match="This field is required."):
            f.clean("")

        with pytest.raises(ValidationError, match="Enter a valid date."):
            f.clean("hello")

        with pytest.raises(
            ValidationError,
            match="['Enter day as a number.', 'Enter month as a number.', 'Enter year as a number.']",
        ):
            f.clean(["a", "b", "c"])

        with pytest.raises(
            ValidationError,
            match="['Enter day as a number.', 'Enter month as a number.', 'Enter year as a number.']",
        ):
            f.clean(["", "", ""])

        with pytest.raises(
            ValidationError,
            match="['Day should be between 1 and 31.', 'Month should be between 1 and 12.', 'Year should be between 1900 and 2025.']",
        ):
            f.clean([0, 13, 1800])

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
            """
            <div>
                <fieldset>
                    <legend>Date:</legend>
                    <input type="number" name="date_0" min="1" max="31" required id="id_date_0">
                    <input type="number" name="date_1" min="1" max="12" required id="id_date_1">
                    <input type="number" name="date_2" min="1900" max="2026" required id="id_date_2">
                </fieldset>
            </div>
            """,
        )

    def test_default_django_render_in_bound_form(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2025"})

        assertHTMLEqual(
            str(f),
            """
            <div>
                <fieldset>
                    <legend>Date:</legend>
                    <input type="number" name="date_0" min="1" max="31" value="1" required id="id_date_0">
                    <input type="number" name="date_1" min="1" max="12" value="12" required id="id_date_1">
                    <input type="number" name="date_2" min="1900" max="2026" value="2025" required id="id_date_2">
                </fieldset>
            </div>
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

    def test_form_errors(self):
        class TestForm(Form):
            date = SplitDateField(max_value=datetime.date(2026, 12, 31))

        f = TestForm({"date_0": "1", "date_1": "12", "date_2": "2027"})
        assert not f.is_valid()
        assert f.errors == {"date": ["Year should be between 1900 and 2025."]}
