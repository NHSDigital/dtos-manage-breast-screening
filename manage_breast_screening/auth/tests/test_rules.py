import pytest

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.auth.rules import (
    is_administrative,
    is_clinical,
    is_sysadmin,
)
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestIsClinical:
    def test_returns_true_for_clinical_assignment(self):
        user_assignment = UserAssignmentFactory.create(clinical=True)
        user_assignment.make_current()

        assert is_clinical(user_assignment.user)

    def test_returns_false_when_no_provider(self):
        user_assignment = UserAssignmentFactory.create()

        assert not is_clinical(user_assignment.user)

    def test_returns_false_for_non_clinical_assignment(self):
        user_assignment = UserAssignmentFactory.create(administrative=True)
        user_assignment.make_current()

        assert not is_clinical(user_assignment.user)

    def test_returns_false_for_no_assigned_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not is_clinical(user_assignment.user)


@pytest.mark.django_db
class TestIsAdministrative:
    def test_returns_true_for_administrative_assignment(self):
        user_assignment = UserAssignmentFactory.create(administrative=True)
        user_assignment.make_current()

        assert is_administrative(user_assignment.user)

    def test_returns_false_when_no_provider(self):
        user_assignment = UserAssignmentFactory.create()

        assert not is_administrative(user_assignment.user)

    def test_returns_false_for_non_administrative_assignment(self):
        user_assignment = UserAssignmentFactory.create(clinical=True)
        user_assignment.make_current()

        assert not is_administrative(user_assignment.user)

    def test_returns_false_for_no_assigned_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not is_administrative(user_assignment.user)


@pytest.mark.django_db
class TestViewParticipantDataPermission:
    def test_returns_true_for_clinical_user(self):
        user_assignment = UserAssignmentFactory.create(clinical=True)
        user_assignment.make_current()

        assert user_assignment.user.has_perm(Permission.VIEW_PARTICIPANT_DATA)

    def test_returns_true_for_administrative_user(self):
        user_assignment = UserAssignmentFactory.create(administrative=True)
        user_assignment.make_current()

        assert user_assignment.user.has_perm(Permission.VIEW_PARTICIPANT_DATA)

    def test_returns_false_for_user_without_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.VIEW_PARTICIPANT_DATA)

    def test_returns_false_if_no_provider_given(self):
        user_assignment = UserAssignmentFactory.create()

        assert not user_assignment.user.has_perm(Permission.VIEW_PARTICIPANT_DATA)


@pytest.mark.django_db
class TestIsSysadmin:
    def test_returns_true_for_sysadmin_user(self):
        user = UserFactory.create(is_sysadmin=True)

        assert is_sysadmin(user)

    def test_returns_false_for_non_sysadmin_user(self):
        user = UserFactory.create(is_sysadmin=False)

        assert not is_sysadmin(user)


@pytest.mark.django_db
class TestManageProviderSettingsPermission:
    def test_returns_true_for_sysadmin(self):
        user = UserFactory.create(is_sysadmin=True)

        assert user.has_perm(Permission.MANAGE_PROVIDER_SETTINGS)

    def test_returns_false_for_non_sysadmin(self):
        user = UserFactory.create(is_sysadmin=False)

        assert not user.has_perm(Permission.MANAGE_PROVIDER_SETTINGS)

    def test_returns_false_for_administrative_user(self):
        user_assignment = UserAssignmentFactory.create(administrative=True)
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.MANAGE_PROVIDER_SETTINGS)
