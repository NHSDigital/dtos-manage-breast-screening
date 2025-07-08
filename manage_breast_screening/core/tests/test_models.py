import pytest
from django.db import models

from ..models import BaseModel


class TestBaseModel:
    @pytest.fixture
    def model(self):
        class Model(BaseModel):
            text = models.TextField(null=False)
            char = models.CharField()

        return Model

    def test_clean(self, model):
        instance = model(text=" abc ", char="   def")
        instance.clean()
        assert instance.text == "abc"
        assert instance.char == "def"
