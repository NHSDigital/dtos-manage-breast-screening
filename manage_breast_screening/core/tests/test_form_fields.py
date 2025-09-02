import datetime

import pytest
from django.core.exceptions import ValidationError
from django.forms import Form
from django.forms.widgets import (
    CheckboxSelectMultiple,
    Select,
    TelInput,
    Textarea,
    TextInput,
)
from pytest_django.asserts import assertHTMLEqual

from ..form_fields import (
    CharField,
    ChoiceField,
    IntegerField,
    MultipleChoiceField,
    SplitDateField,
)


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
            telephone_field = CharField(label="Ring ring", widget=TelInput)
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

    def test_telinput_renders_input_with_type_tel(self, form_class):
        assertHTMLEqual(
            form_class()["telephone_field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_telephone_field">
                    Ring ring
                </label><input type="tel" class="nhsuk-input" id="id_telephone_field" name="telephone_field">
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
                    <textarea class="nhsuk-textarea" id="id_textfield" name="textfield" rows="3" autocomplete="autocomplete" spellcheck="true"></textarea>
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
                    <textarea class="nhsuk-textarea" id="id_textfield_simple" name="textfield_simple" rows="10"></textarea>
                </div>
                """,
        )


class TestIntegerField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = IntegerField(label="Abc", initial=1, max_value=10)

        return TestForm

    def test_renders_nhs_input(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label><input class="nhsuk-input" id="id_field" name="field" type="number" value="1">
            </div>
            """,
        )


class TestChoiceField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = ChoiceField(
                label="Abc",
                label_classes="app-abc",
                choices=(("a", "A"), ("b", "B")),
                hint="Pick either one",
            )
            select_field = ChoiceField(
                label="Select",
                label_classes="app-select",
                choices=(("a", "A"), ("b", "B")),
                hint="Pick either one",
                widget=Select,
            )
            details = CharField(label="Abc", initial="")

        return TestForm

    def test_renders_nhs_radios(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <fieldset aria-describedby="id_field-hint" class="nhsuk-fieldset">
                    <legend class="nhsuk-fieldset__legend app-abc">
                        Abc
                    </legend>
                    <div class="nhsuk-hint" id="id_field-hint">
                        Pick either one
                    </div>
                    <div class="nhsuk-radios" data-module="nhsuk-radios">
                        <div class="nhsuk-radios__item">
                            <input class="nhsuk-radios__input" id="id_field" name="field" type="radio" value="a">
                            <label class="nhsuk-label nhsuk-radios__label" for="id_field">A</label>
                        </div>
                        <div class="nhsuk-radios__item">
                            <input class="nhsuk-radios__input" id="id_field-2" name="field" type="radio" value="b">
                            <label class="nhsuk-label nhsuk-radios__label" for="id_field-2">B</label>
                        </div>
                    </div>
                </fieldset>
            </div>
            """,
        )

    def test_renders_radios_with_conditional_html(self, form_class):
        form = form_class()
        form["field"].add_conditional_html("b", "<p>Hello</p>")

        assertHTMLEqual(
            form["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <fieldset aria-describedby="id_field-hint" class="nhsuk-fieldset">
                    <legend class="nhsuk-fieldset__legend app-abc">
                        Abc
                    </legend>
                    <div class="nhsuk-hint" id="id_field-hint">
                        Pick either one
                    </div>
                    <div class="nhsuk-radios nhsuk-radios--conditional" data-module="nhsuk-radios">
                        <div class="nhsuk-radios__item">
                            <input class="nhsuk-radios__input" id="id_field" name="field" type="radio" value="a">
                            <label class="nhsuk-label nhsuk-radios__label" for="id_field">A</label>
                        </div>
                        <div class="nhsuk-radios__item">
                            <input aria-controls="conditional-id_field-2" aria-expanded="false" class="nhsuk-radios__input" id="id_field-2" name="field" type="radio" value="b">
                            <label class="nhsuk-label nhsuk-radios__label" for="id_field-2">B</label>
                        </div>
                        <div class="nhsuk-radios__conditional nhsuk-radios__conditional--hidden" id="conditional-id_field-2">
                            <p>Hello</p>
                        </div>
                    </div>
                </fieldset>
            </div>
            """,
        )

    def test_renders_nhs_select(self, form_class):
        assertHTMLEqual(
            form_class()["select_field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label app-select"  for="id_select_field">Select</label>
                <div class="nhsuk-hint" id="id_select_field-hint">
                    Pick either one
                </div>
                <select aria-describedby="id_select_field-hint" class="nhsuk-select" id="id_select_field" name="select_field">
                    <option value="a">A</option>
                    <option value="b">B</option>
                </select>
            </div>
            """,
        )

    def test_renders_select_with_conditional_html(self, form_class):
        form = form_class()

        with pytest.raises(ValueError):
            form["select_field"].add_conditional_html("b", "<p>Hello</p>")

    def test_adding_dividers_via_boundfield(self, form_class):
        bound_field = form_class()["field"]
        bound_field.add_divider_after("a", "or")
        assert bound_field.get_divider_after("a") == "or"


class TestMultipleChoiceField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            checkbox_field = MultipleChoiceField(
                label="Def",
                label_classes="app-def",
                choices=(("a", "A"), ("b", "B")),
                hint="Pick any number",
                widget=CheckboxSelectMultiple,
            )
            details = CharField(label="Abc", initial="")

        return TestForm

    def test_renders_nhs_checkboxes(self, form_class):
        assertHTMLEqual(
            form_class()["checkbox_field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <fieldset aria-describedby="id_checkbox_field-hint" class="nhsuk-fieldset">
                    <legend class="nhsuk-fieldset__legend app-def">
                        Def
                    </legend>
                    <div class="nhsuk-hint" id="id_checkbox_field-hint">
                        Pick any number
                    </div>
                    <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                        <div class="nhsuk-checkboxes__item">
                            <input class="nhsuk-checkboxes__input" id="id_checkbox_field" name="checkbox_field" type="checkbox" value="a">
                            <label class="nhsuk-label nhsuk-checkboxes__label" for="id_checkbox_field">A</label>
                        </div>
                        <div class="nhsuk-checkboxes__item">
                            <input class="nhsuk-checkboxes__input" id="id_checkbox_field-2" name="checkbox_field" type="checkbox" value="b">
                            <label class="nhsuk-label nhsuk-checkboxes__label" for="id_checkbox_field-2">B</label>
                        </div>
                    </div>
                </fieldset>
            </div>
            """,
        )

    def test_renders_nhs_checkboxes_with_conditional_html(self, form_class):
        form = form_class()
        form["checkbox_field"].add_conditional_html("b", "<p>Hello</p>")

        assertHTMLEqual(
            form["checkbox_field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <fieldset aria-describedby="id_checkbox_field-hint" class="nhsuk-fieldset">
                    <legend class="nhsuk-fieldset__legend app-def">
                        Def
                    </legend>
                    <div class="nhsuk-hint" id="id_checkbox_field-hint">
                        Pick any number
                    </div>
                    <div class="nhsuk-checkboxes nhsuk-checkboxes--conditional" data-module="nhsuk-checkboxes">
                        <div class="nhsuk-checkboxes__item">
                            <input class="nhsuk-checkboxes__input" id="id_checkbox_field" name="checkbox_field" type="checkbox" value="a">
                            <label class="nhsuk-label nhsuk-checkboxes__label" for="id_checkbox_field">A</label>
                        </div>
                        <div class="nhsuk-checkboxes__item">
                            <input aria-controls="conditional-id_checkbox_field-2" aria-expanded="false" class="nhsuk-checkboxes__input" id="id_checkbox_field-2" name="checkbox_field" type="checkbox" value="b">
                            <label class="nhsuk-label nhsuk-checkboxes__label" for="id_checkbox_field-2">B</label>
                        </div>
                        <div class="nhsuk-checkboxes__conditional nhsuk-checkboxes__conditional--hidden" id="conditional-id_checkbox_field-2">
                            <p>Hello</p>
                        </div>
                    </div>
                </fieldset>
            </div>
            """,
        )
