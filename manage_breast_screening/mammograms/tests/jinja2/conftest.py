from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from django.conf import settings
from jinja2 import ChainableUndefined, Environment, FileSystemLoader

from manage_breast_screening.config.jinja2_env import environment
from manage_breast_screening.participants.models.appointment import Appointment


@pytest.fixture
def jinja_env() -> Environment:
    return environment(
        loader=FileSystemLoader(settings.BASE_DIR / "mammograms" / "jinja2"),
        undefined=ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


@pytest.fixture
def mock_appointment():
    mock_appointment = MagicMock(spec=Appointment)
    mock_appointment.pk = "53ce8d3b-9e65-471a-b906-73809c0475d0"
    mock_appointment.screening_episode.participant.nhs_number = "99900900829"
    mock_appointment.screening_episode.participant.pk = uuid4()
    mock_appointment.screening_episode.participant.phone = "01234123456"
    return mock_appointment
