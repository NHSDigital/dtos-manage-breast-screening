import pytest
from django.forms import Form
from django.template.loader import render_to_string
from pytest_django.asserts import assertHTMLEqual

from ...fields import IntegerField, StepperInput, YearField


class TestIntegerField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = IntegerField(
                label="Abc",
                initial=1,
                max_value=10,
                visually_hidden_label_prefix="prefix: ",
                visually_hidden_label_suffix=" - suffix",
            )
            stepper_field = IntegerField(
                label="Stepper",
                initial=1,
                min_value=0,
                max_value=10,
                widget=StepperInput,
            )

        return TestForm

    def test_renders_nhs_input(self, form_class):
        actual = form_class()["field"].as_field_group()
        expected = render_to_string(
            "nhsuk/components/input/template.jinja",
            {
                "params": {
                    "label": {
                        "html": '<span class="nhsuk-u-visually-hidden">prefix: </span>Abc<span class="nhsuk-u-visually-hidden"> - suffix</span>'
                    },
                    "id": "id_field",
                    "name": "field",
                    "inputmode": "numeric",
                    "type": "number",
                    "value": 1,
                }
            },
        )
        assertHTMLEqual(actual, expected)

    def test_renders_stepper_input(self, form_class):
        actual = form_class()["stepper_field"].as_field_group()
        expected = render_to_string(
            "components/stepper-input/template.jinja",
            {
                "params": {
                    "label": {"text": "Stepper"},
                    "id": "id_stepper_field",
                    "name": "stepper_field",
                    "value": 1,
                    "min": 0,
                    "max": 10,
                }
            },
        )
        assertHTMLEqual(actual, expected)


class TestYearField:
    def test_uses_callable_bounds(self):
        bounds = {"min": 2000, "max": 2005}

        class TestForm(Form):
            field = YearField(
                min_value_callable=lambda: bounds["min"],
                max_value_callable=lambda: bounds["max"],
            )

        assert TestForm(data={"field": 2003}).is_valid()

        bounds["max"] = 2002
        form = TestForm(data={"field": 2003})
        assert not form.is_valid()
        assert form.errors["field"] == ["Year must be 2002 or earlier"]

        bounds["min"] = 2000
        form = TestForm(data={"field": 1999})

        assert not form.is_valid()
        assert form.errors["field"] == ["Year must be 2000 or later"]
