import pytest
from django.forms import Form
from pytest_django.asserts import assertHTMLEqual

from ...fields import IntegerField


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
