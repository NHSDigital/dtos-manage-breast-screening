import pytest
from django.forms import Form
from django.forms.widgets import CheckboxSelectMultiple, Select
from pytest_django.asserts import assertHTMLEqual

from ...fields import CharField, ChoiceField, MultipleChoiceField


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
