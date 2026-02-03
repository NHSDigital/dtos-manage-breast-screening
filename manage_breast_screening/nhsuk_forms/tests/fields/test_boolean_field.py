import pytest
from django.forms import Form
from django.template.loader import render_to_string
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
        actual = form_class()["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/checkboxes/template.jinja",
            {
                "params": {
                    "name": "field",
                    "idPrefix": "id_field",
                    "items": [
                        {
                            "id": "id_field",
                            "value": "true",
                            "text": "Abc",
                            "checked": False,
                            "hint": {"html": "Click me"},
                        }
                    ],
                }
            },
        )
        assertHTMLEqual(actual, expected)

    def test_renders_with_data_true(self, form_class):
        actual = form_class(data={"field": "true"})["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/checkboxes/template.jinja",
            {
                "params": {
                    "name": "field",
                    "idPrefix": "id_field",
                    "items": [
                        {
                            "id": "id_field",
                            "value": "true",
                            "text": "Abc",
                            "checked": True,
                            "hint": {"html": "Click me"},
                        }
                    ],
                }
            },
        )
        assertHTMLEqual(actual, expected)

    def test_renders_with_data_false(self, form_class):
        actual = form_class(data={"field": "false"})["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/checkboxes/template.jinja",
            {
                "params": {
                    "name": "field",
                    "idPrefix": "id_field",
                    "items": [
                        {
                            "id": "id_field",
                            "value": "true",
                            "text": "Abc",
                            "checked": False,
                            "hint": {"html": "Click me"},
                        }
                    ],
                }
            },
        )
        assertHTMLEqual(actual, expected)

    def test_renders_with_initial_true(self, form_class):
        actual = form_class(initial={"field": True})["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/checkboxes/template.jinja",
            {
                "params": {
                    "name": "field",
                    "idPrefix": "id_field",
                    "items": [
                        {
                            "id": "id_field",
                            "value": "true",
                            "text": "Abc",
                            "checked": True,
                            "hint": {"html": "Click me"},
                        }
                    ],
                }
            },
        )
        assertHTMLEqual(actual, expected)

    def test_renders_with_initial_false(self, form_class):
        actual = form_class(initial={"field": False})["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/checkboxes/template.jinja",
            {
                "params": {
                    "name": "field",
                    "idPrefix": "id_field",
                    "items": [
                        {
                            "id": "id_field",
                            "value": "true",
                            "text": "Abc",
                            "checked": False,
                            "hint": {"html": "Click me"},
                        }
                    ],
                }
            },
        )
        assertHTMLEqual(actual, expected)
