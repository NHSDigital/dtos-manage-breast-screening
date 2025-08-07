from unittest import TestCase

import pytest
from django.conf import settings
from jinja2 import ChainableUndefined, Environment, FileSystemLoader

from manage_breast_screening.config.jinja2_env import environment

TestCase.maxDiff = None


@pytest.fixture
def jinja_env() -> Environment:
    return environment(
        loader=FileSystemLoader(settings.BASE_DIR / "participants" / "jinja2"),
        undefined=ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
