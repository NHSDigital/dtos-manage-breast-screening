import datetime

import pytest
from django.core.exceptions import ValidationError
from django.forms import Form, Textarea, TextInput
from pytest_django.asserts import assertHTMLEqual

from ..form_fields import CharField, SplitDateField


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


class TestCharField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = CharField(label="Abc", initial="somevalue", max_length=10)
            field_with_visually_hidden_label = CharField(
                label="Abc",
                initial="somevalue",
                label_classes="nhsuk-u-visually-hidden",
            )
            field_with_hint = CharField(
                label="With hint", initial="", hint="ALL UPPERCASE"
            )
            field_with_classes = CharField(
                label="With classes", initial="", classes="nhsuk-u-width-two-thirds"
            )
            field_with_extra_attrs = CharField(
                label="Extra",
                widget=TextInput(
                    attrs=dict(
                        autocomplete="off",
                        inputmode="numeric",
                        spellcheck="false",
                        autocapitalize="none",
                        pattern=r"\d{3}",
                    )
                ),
            )
            textfield = CharField(
                label="Text",
                widget=Textarea(
                    attrs={
                        "rows": "3",
                        "autocomplete": "autocomplete",
                        "spellcheck": "true",
                    }
                ),
            )
            textfield_simple = CharField(label="Text", widget=Textarea)

        return TestForm

    def test_renders_nhs_input(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label><input class="nhsuk-input" id="id_field" name="field" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_visually_hidden_label(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_visually_hidden_label"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label nhsuk-u-visually-hidden" for="id_field_with_visually_hidden_label">
                    Abc
                </label><input class="nhsuk-input" id="id_field_with_visually_hidden_label" name="field_with_visually_hidden_label" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_hint(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_hint"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_hint">
                    With hint
                </label>
                <div class="nhsuk-hint" id="id_field_with_hint-hint">ALL UPPERCASE</div>
                <input class="nhsuk-input" id="id_field_with_hint" name="field_with_hint" type="text" aria-describedby="id_field_with_hint-hint">
            </div>
            """,
        )

    def test_renders_nhs_input_with_classes(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_classes"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_classes">
                    With classes
                </label>
                <input class="nhsuk-input nhsuk-u-width-two-thirds" id="id_field_with_classes" name="field_with_classes" type="text">
            </div>
            """,
        )

    def test_renders_nhs_input_with_extra_attrs(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_extra_attrs"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_extra_attrs">
                    Extra
                </label>
                <input autocomplete="off" autocapitalize="none" spellcheck="false" inputmode="numeric" pattern="\\d{3}" class="nhsuk-input" id="id_field_with_extra_attrs" name="field_with_extra_attrs" type="text">
            </div>
            """,
        )

    def test_bound_value_reflected_in_html_value(self, form_class):
        assertHTMLEqual(
            form_class({"field": "othervalue"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label><input class="nhsuk-input" id="id_field" name="field" type="text" value="othervalue">
            </div>
            """,
        )

    def test_invalid_value_renders_validation_error(self, form_class):
        assertHTMLEqual(
            form_class({"field": "reallylongvalue"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group nhsuk-form-group--error">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label>
                <span class="nhsuk-error-message" id="id_field-error">
                <span class="nhsuk-u-visually-hidden">Error:</span> Ensure this value has at most 10 characters (it has 15).</span>
                <input class="nhsuk-input nhsuk-input--error" id="id_field" name="field" type="text" value="reallylongvalue" aria-describedby="id_field-error">
            </div>
            """,
        )

    def test_textarea_renders_textarea(self, form_class):
        assertHTMLEqual(
            form_class()["textfield"].as_field_group(),
            """
                <div class="nhsuk-form-group">
                    <label class="nhsuk-label" for="id_textfield">
                        Text
                    </label>
                    <textarea class="nhsuk-textarea" id="id_textfield" name="textfield" rows=" 3 " autocomplete="autocomplete" spellcheck="true"></textarea>
                </div>
                """,
        )

    def test_textarea_class_renders_textarea(self, form_class):
        assertHTMLEqual(
            form_class()["textfield_simple"].as_field_group(),
            """
                <div class="nhsuk-form-group">
                    <label class="nhsuk-label" for="id_textfield_simple">
                        Text
                    </label>
                    <textarea class="nhsuk-textarea" id="id_textfield_simple" name="textfield_simple" rows=" 10 "></textarea>
                </div>
                """,
        )
