from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import ProviderFactory


class TestUser:
    def test_setting_current_provider(self):
        user = UserFactory.build()
        provider = ProviderFactory.build()
        assert user.current_provider is None

        user.current_provider = provider

        assert user.current_provider is provider
