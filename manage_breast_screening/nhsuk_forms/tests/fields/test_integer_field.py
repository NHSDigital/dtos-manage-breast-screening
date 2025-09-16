import pytest
from django.forms import Form
from pytest_django.asserts import assertHTMLEqual

from ...fields import IntegerField


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
