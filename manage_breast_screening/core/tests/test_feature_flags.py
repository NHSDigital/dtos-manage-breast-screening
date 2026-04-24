import pytest
from openfeature import api

from manage_breast_screening.core.apps import _FLAGS_YAML
from manage_breast_screening.core.feature_flags import setup_feature_flags


class TestSetupFeatureFlags:
    @pytest.fixture(autouse=True)
    def reset_flags(self):
        yield
        setup_feature_flags(_FLAGS_YAML)

    def test_enabled_flag_returns_true(self, tmp_path):
        flags_file = tmp_path / "flags.yml"
        flags_file.write_text("flags:\n  my_flag: true\n")
        setup_feature_flags(flags_file)

        assert api.get_client().get_boolean_value("my_flag", False) is True

    def test_disabled_flag_returns_false(self, tmp_path):
        flags_file = tmp_path / "flags.yml"
        flags_file.write_text("flags:\n  my_flag: false\n")
        setup_feature_flags(flags_file)

        assert api.get_client().get_boolean_value("my_flag", False) is False

    def test_missing_flag_returns_fallback(self, tmp_path):
        flags_file = tmp_path / "flags.yml"
        flags_file.write_text("flags: {}\n")
        setup_feature_flags(flags_file)

        assert api.get_client().get_boolean_value("nonexistent_flag", False) is False


class TestWithFlagEnabledFixture:
    def test_enabled_flag_returns_true(self, with_flag_enabled):
        with_flag_enabled("my_flag")

        assert api.get_client().get_boolean_value("my_flag", False) is True

    def test_unenabled_flag_returns_fallback(self, with_flag_enabled):
        assert api.get_client().get_boolean_value("my_flag", False) is False

    def test_multiple_flags_can_be_enabled(self, with_flag_enabled):
        with_flag_enabled("flag_one")
        with_flag_enabled("flag_two")

        assert api.get_client().get_boolean_value("flag_one", False) is True
        assert api.get_client().get_boolean_value("flag_two", False) is True

    def test_enabling_one_flag_does_not_enable_others(self, with_flag_enabled):
        with_flag_enabled("flag_one")

        assert api.get_client().get_boolean_value("flag_two", False) is False
