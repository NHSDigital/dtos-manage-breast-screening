from datetime import datetime, timezone
from textwrap import dedent
from uuid import uuid4

import pytest
from pytest_django.asserts import assertInHTML

from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter

from ..factories import ParticipantReportedMammogramFactory


class TestScreeningDetails:
    @pytest.fixture
    def presented_mammograms(self):
        mammogram = ParticipantReportedMammogramFactory.build(
            outside_uk=True,
            location_details="france",
            approx_date="2021",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        return LastKnownMammogramPresenter(
            [mammogram], participant_pk=uuid4(), current_url="/"
        )

    def test_screening_details(self, presented_mammograms, jinja_env, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, tzinfo=timezone.utc))

        template = jinja_env.from_string(
            dedent(
                r"""
                {% from 'components/participant-details/screening_details.jinja' import screening_details %}
                {{ screening_details(presented_mammograms=presented_mammograms, screening_protocol='Family history') }}
                """
            )
        )

        response = template.render({"presented_mammograms": presented_mammograms})

        assertInHTML(
            '<h2 class="nhsuk-card__heading">Screening details</h2>',
            response,
        )

        assertInHTML(
            '<dt class="nhsuk-summary-list__key">Screening protocol</dt>', response
        )
        assertInHTML(
            '<dd class="nhsuk-summary-list__value">Family history</dd>',
            response,
        )

        assertInHTML(
            '<dt class="nhsuk-summary-list__key">Last known mammograms</dt>', response
        )
        assertInHTML(
            """
            <dd class="nhsuk-summary-list__value">
                <div data-testid="mammograms">
                    <p>
                        <span class="nhsuk-u-font-weight-bold">Added today</span><br>
                        Approximate date: 2021<br>
                        Outside the UK: france
                    </p>
                </div>
            </dd>
            """,
            response,
        )
