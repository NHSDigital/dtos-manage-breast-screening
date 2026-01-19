import pytest

from manage_breast_screening.clinics.tests.factories import ProviderFactory
from manage_breast_screening.users.models import User
from manage_breast_screening.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserManager:
    def test_create_user(self):
        user = User.objects.create_user(
            nhs_uid="123456789012",
            email="test@example.com",
            first_name="Jane",
            last_name="Doe",
        )

        assert user.pk is not None
        assert user.nhs_uid == "123456789012"
        assert user.email == "test@example.com"
        assert user.first_name == "Jane"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.has_usable_password() is False

    def test_create_user_with_none_email(self):
        user = User.objects.create_user(nhs_uid="123456789012", email=None)

        assert user.pk is not None
        assert user.email == ""

    def test_create_user_without_nhs_uid_raises_error(self):
        with pytest.raises(ValueError, match="The NHS UID must be set"):
            User.objects.create_user(nhs_uid="")


class TestUser:
    def test_setting_current_provider(self):
        user = UserFactory.build()
        provider = ProviderFactory.build()
        assert user.current_provider is None

        user.current_provider = provider

        assert user.current_provider is provider
