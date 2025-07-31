from textwrap import dedent

import pytest
from pytest_django.asserts import assertInHTML

from manage_breast_screening.participants.presenters import ParticipantPresenter

from ..factories import ParticipantFactory


class TestPersonalDetails:
    @pytest.fixture
    def presenter(self):
        return ParticipantPresenter(
            ParticipantFactory.build(
                ethnic_background_id="english_welsh_scottish_ni_british"
            )
        )

    def test_personal_details(self, presenter, jinja_env):
        template = jinja_env.from_string(
            dedent(
                r"""
                {% from 'components/participant-details/personal_details.jinja' import personal_details %}
                {{ personal_details(presenter) }}
                """
            )
        )

        response = template.render({"presenter": presenter})

        assertInHTML(
            '<h2 class="nhsuk-card__heading">Personal details</h2>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">NHS Number</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.nhs_number}</dd>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Full name</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.full_name}</dd>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Gender</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.gender}</dd>', response
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Date of birth</dt>', response)
        assertInHTML(
            f'<dd class="nhsuk-summary-list__value">{presenter.date_of_birth}<br><span class="nhsuk-hint">({presenter.age})</span></dd>',
            response,
        )

        assertInHTML('<dt class="nhsuk-summary-list__key">Ethnicity</dt>', response)
        assertInHTML(
            '<dd class="nhsuk-summary-list__value">White (English, Welsh, Scottish, Northern Irish or British)</dd>',
            response,
        )
