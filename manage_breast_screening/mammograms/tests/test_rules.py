import pytest

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


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
    @pytest.fixture
    def scheduled_appointment(self):
        return AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )

    @pytest.fixture
    def checked_in_appointment(self):
        return AppointmentFactory.create(
            current_status=AppointmentStatusNames.CHECKED_IN
        )

    @pytest.fixture
    def screened_appointment(self):
        return AppointmentFactory.create(current_status=AppointmentStatusNames.SCREENED)

    @pytest.fixture
    def in_progress_appointment(self):
        return AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )

    def test_can_start_if_user_is_clinical(self, clinical_user):
        assert clinical_user.has_perm(Permission.START_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_for_administrative_user(self, administrative_user):
        assert not administrative_user.has_perm(Permission.START_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_for_user_without_roles(self):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(Permission.START_MAMMOGRAM_APPOINTMENT)

    def test_cannot_start_if_no_current_provider(self):
        user_assignment = UserAssignmentFactory.create()

        assert not user_assignment.user.has_perm(Permission.START_MAMMOGRAM_APPOINTMENT)
