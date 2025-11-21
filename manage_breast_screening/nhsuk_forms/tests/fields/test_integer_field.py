import pytest
from django.forms import Form
from pytest_django.asserts import assertHTMLEqual

from ...fields import IntegerField, YearField


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

        return TestForm

    def test_renders_nhs_input(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    <span class="nhsuk-u-visually-hidden">prefix: </span>Abc<span class="nhsuk-u-visually-hidden"> - suffix</span>
                </label><input class="nhsuk-input" id="id_field" name="field" type="number" value="1" inputmode="numeric">
            </div>
            """,
        )


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
