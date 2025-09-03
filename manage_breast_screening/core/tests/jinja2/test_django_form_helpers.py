from textwrap import dedent

from django.forms import ChoiceField, Form


class ABForm(Form):
    ab_choice = ChoiceField(choices=(("a", "A"), ("b", "B")))


class TestDjangoFormHelpers:
    def test_blank_error_summary(self, jinja_env):
        form = ABForm()

        template = jinja_env.from_string(
            dedent(
                r"""
                    {% from 'django_form_helpers.jinja' import form_error_summary %}
                    {{ form_error_summary(form) }}
                    """
            )
        )

        response = template.render({"form": form})

        assert dedent(response).strip() == ""

    def test_error_summary(self, jinja_env):
        form = ABForm({})

        template = jinja_env.from_string(
            dedent(
                r"""
                    {% from 'django_form_helpers.jinja' import form_error_summary %}
                    {{ form_error_summary(form) }}
                    """
            )
        )

        response = template.render({"form": form})

        assert (
            dedent(response).strip()
            == dedent(
                """
                <div class="nhsuk-error-summary" aria-labelledby="error-summary-title" role="alert" tabindex="-1" data-module="nhsuk-error-summary">
                  <h2 class="nhsuk-error-summary__title" id="error-summary-title">
                    There is a problem
                  </h2>
                  <div class="nhsuk-error-summary__body">
                    <ul class="nhsuk-list nhsuk-error-summary__list" role="list">      <li>        <a href="#id_ab_choice">This field is required.</a>
                </li>    </ul>
                  </div>
                </div>
                """
            ).strip()
        )
