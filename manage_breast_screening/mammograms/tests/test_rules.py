import pytest

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory


@pytest.mark.django_db
class TestViewMammogramAppointmentPermission:
    def test_returns_true_for_clinical_user(self):
        user_assignment = UserAssignmentFactory.create(clinical=True)
        user_assignment.make_current()

        assert user_assignment.user.has_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT)

    def test_returns_false_for_administrative_user(self):
        user_assignment = UserAssignmentFactory.create(administrative=True)
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT)

    def test_returns_false_for_user_without_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT)

    def test_returns_false_if_no_provider_given(self):
        user_assignment = UserAssignmentFactory.create()

        assert not user_assignment.user.has_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT)


@pytest.mark.django_db
class TestAppointmentActionPermissions:
    def test_can_start_if_user_is_clinical(self, clinical_user):
        assert clinical_user.has_perm(Permission.DO_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_for_administrative_user(self, administrative_user):
        assert not administrative_user.has_perm(Permission.DO_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_for_user_without_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.DO_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_if_no_current_provider(self):
        user_assignment = UserAssignmentFactory.create()

        assert not user_assignment.user.has_perm(Permission.DO_MAMMOGRAM_APPOINTMENT)
