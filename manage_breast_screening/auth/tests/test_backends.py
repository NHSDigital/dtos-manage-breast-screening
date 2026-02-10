import pytest

from manage_breast_screening.users.tests.factories import UserFactory

from ..backends import CIS2Backend


@pytest.mark.django_db
class TestCIS2BackendAuthenticate:
    def test_creates_user_from_cis2_userinfo(self):
        backend = CIS2Backend()

        user = backend.authenticate(
            None,
            cis2_sub="test-sub-123",
            cis2_userinfo={
                "email": "jane@nhs.net",
                "given_name": "Jane",
                "family_name": "Doe",
            },
        )

        assert user is not None
        assert user.nhs_uid == "test-sub-123"
        assert user.email == "jane@nhs.net"
        assert user.first_name == "Jane"
        assert user.last_name == "Doe"

    def test_updates_existing_user(self):
        existing = UserFactory.create(
            nhs_uid="test-sub-123",
            first_name="Old",
            last_name="Name",
        )
        backend = CIS2Backend()

        user = backend.authenticate(
            None,
            cis2_sub="test-sub-123",
            cis2_userinfo={
                "email": "new@nhs.net",
                "given_name": "New",
                "family_name": "Name",
            },
        )

        assert user.pk == existing.pk
        assert user.email == "new@nhs.net"
        assert user.first_name == "New"

    def test_returns_none_when_cis2_sub_is_none(self):
        backend = CIS2Backend()

        result = backend.authenticate(
            None,
            cis2_sub=None,
            cis2_userinfo={"email": "test@nhs.net"},
        )

        assert result is None

    def test_returns_none_when_cis2_userinfo_is_none(self):
        backend = CIS2Backend()

        result = backend.authenticate(
            None,
            cis2_sub="test-sub-123",
            cis2_userinfo=None,
        )

        assert result is None

    def test_handles_missing_userinfo_fields(self):
        backend = CIS2Backend()

        user = backend.authenticate(
            None,
            cis2_sub="test-sub-123",
            cis2_userinfo={},
        )

        assert user is not None
        assert user.nhs_uid == "test-sub-123"
        assert user.email == ""
        assert user.first_name == ""
        assert user.last_name == ""

    def test_handles_empty_userinfo_fields(self):
        backend = CIS2Backend()

        user = backend.authenticate(
            None,
            cis2_sub="test-sub-123",
            cis2_userinfo={
                "email": "",
                "given_name": "",
                "family_name": "",
            },
        )

        assert user is not None
        assert user.nhs_uid == "test-sub-123"
        assert user.email == ""
        assert user.first_name == ""
        assert user.last_name == ""


@pytest.mark.django_db
class TestCIS2BackendGetUser:
    def test_returns_active_user(self):
        user = UserFactory.create(is_active=True)
        backend = CIS2Backend()

        result = backend.get_user(user.pk)

        assert result == user

    def test_returns_none_for_inactive_user(self):
        user = UserFactory.create(is_active=False)
        backend = CIS2Backend()

        result = backend.get_user(user.pk)

        assert result is None

    def test_returns_none_for_nonexistent_user(self):
        backend = CIS2Backend()

        result = backend.get_user(99999)

        assert result is None
