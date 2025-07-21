from unittest.mock import MagicMock

import pytest
from django.forms import Form

form = MagicMock(autospec=Form)
form.errors = {}
form_with_errors = MagicMock(autospec=Form)
form_with_errors.errors = {"field": ["mooo"]}


@pytest.mark.parametrize(
    "page_title,form,expected_title",
    [
        ("", None, "Manage breast screening – NHS"),
        ("Page 1", None, "Page 1 – Manage breast screening – NHS"),
        ("Page 2", form_with_errors, "Error: Page 2 – Manage breast screening – NHS"),
        ("Page 3", form, "Page 3 – Manage breast screening – NHS"),
    ],
)
def test_page_title(jinja_env, page_title, form, expected_title):
    template = jinja_env.from_string(
        """
    {% extends "layout-app.jinja" %}
    """
    )
    html = template.render({"page_title": page_title, "form": form})
    assert f"<title>{expected_title}</title>" in html
