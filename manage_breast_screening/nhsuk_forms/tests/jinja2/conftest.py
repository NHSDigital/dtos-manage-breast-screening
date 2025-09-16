import pytest
from django.conf import settings
from jinja2 import ChainableUndefined, Environment, FileSystemLoader

from manage_breast_screening.config.jinja2_env import environment


@pytest.fixture
def jinja_env() -> Environment:
    return environment(
        loader=FileSystemLoader(settings.BASE_DIR / "nhsuk_forms" / "jinja2"),
        undefined=ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
