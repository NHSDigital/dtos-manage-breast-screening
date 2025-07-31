from textwrap import dedent

import pytest
from pytest_django.asserts import assertInHTML

from manage_breast_screening.participants.presenters import ParticipantPresenter

from ..factories import ParticipantFactory


class TestContactDetails:
    @pytest.fixture
    def presenter(self):
        return ParticipantPresenter(
            ParticipantFactory.build(
                address__lines=["line1", "line2"], address__postcode="a123ab"
            )
        )

    def test_contact_details(self, presenter, jinja_env):
        template = jinja_env.from_string(
            dedent(
                r"""
                {% from 'components/participant-details/contact_details.jinja' import contact_details %}
                {{ contact_details(presenter) }}
                """
            )
        )

        response = template.render({"presenter": presenter})

        assertInHTML(
            '<h2 class="nhsuk-card__heading">Contact details</h2>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Address</dt>', response)
        assertInHTML(
            '<dd class="nhsuk-summary-list__value">line1<br>line2<br>a123ab</dd>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Phone</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.phone}</dd>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Email</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.email}</dd>', response
        )
