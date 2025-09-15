import pytest
from django.forms import Form
from pytest_django.asserts import assertHTMLEqual

from ...fields import BooleanField


class TestBooelanField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = BooleanField(
                label="Abc",
                hint="Click me",
                label_classes="extra-class",
                required=False,
            )

        return TestForm

    def test_renders_checkbox(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <div class="nhsuk-hint" id="id_field-hint">
                    Click me
                </div>
                <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                    <div class="nhsuk-checkboxes__item">
                        <input class="nhsuk-checkboxes__input" id="id_field" name="field" type="checkbox" value="true">
                        <label class="nhsuk-label nhsuk-checkboxes__label" for="id_field">Abc</label>
                    </div>
                </div>
            </div>
            """,
        )

    def test_renders_with_data_true(self, form_class):
        assertHTMLEqual(
            form_class(data={"field": "true"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <div class="nhsuk-hint" id="id_field-hint">
                    Click me
                </div>
                <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                    <div class="nhsuk-checkboxes__item">
                        <input checked class="nhsuk-checkboxes__input" id="id_field" name="field" type="checkbox" value="true">
                        <label class="nhsuk-label nhsuk-checkboxes__label" for="id_field">Abc</label>
                    </div>
                </div>
            </div>
            """,
        )

    def test_renders_with_data_false(self, form_class):
        assertHTMLEqual(
            form_class(data={"field": "false"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <div class="nhsuk-hint" id="id_field-hint">
                    Click me
                </div>
                <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                    <div class="nhsuk-checkboxes__item">
                        <input class="nhsuk-checkboxes__input" id="id_field" name="field" type="checkbox" value="true">
                        <label class="nhsuk-label nhsuk-checkboxes__label" for="id_field">Abc</label>
                    </div>
                </div>
            </div>
            """,
        )

    def test_renders_with_initial_true(self, form_class):
        assertHTMLEqual(
            form_class(initial={"field": True})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <div class="nhsuk-hint" id="id_field-hint">
                    Click me
                </div>
                <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                    <div class="nhsuk-checkboxes__item">
                        <input checked class="nhsuk-checkboxes__input" id="id_field" name="field" type="checkbox" value="true">
                        <label class="nhsuk-label nhsuk-checkboxes__label" for="id_field">Abc</label>
                    </div>
                </div>
            </div>
            """,
        )

    def test_renders_with_initial_false(self, form_class):
        assertHTMLEqual(
            form_class(initial={"field": False})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <div class="nhsuk-hint" id="id_field-hint">
                    Click me
                </div>
                <div class="nhsuk-checkboxes" data-module="nhsuk-checkboxes">
                    <div class="nhsuk-checkboxes__item">
                        <input class="nhsuk-checkboxes__input" id="id_field" name="field" type="checkbox" value="true">
                        <label class="nhsuk-label nhsuk-checkboxes__label" for="id_field">Abc</label>
                    </div>
                </div>
            </div>
            """,
        )
