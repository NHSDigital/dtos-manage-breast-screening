import pytest

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.participants.models.appointment import AppointmentStatus
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
class TestStartMammogramAppointmentPermission:
    @pytest.fixture
    def confirmed_appointment(self):
        return AppointmentFactory.create(current_status=AppointmentStatus.CONFIRMED)

    @pytest.fixture
    def checked_in_appointment(self):
        return AppointmentFactory.create(current_status=AppointmentStatus.CHECKED_IN)

    @pytest.fixture
    def screened_appointment(self):
        return AppointmentFactory.create(current_status=AppointmentStatus.SCREENED)

    def test_returns_true_if_user_is_clinical_and_appointment_is_confirmed(
        self, clinical_user, confirmed_appointment
    ):
        assert clinical_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, obj=confirmed_appointment
        )

    def test_returns_true_if_user_is_clinical_and_appointment_is_checked_in(
        self, clinical_user, checked_in_appointment
    ):
        assert clinical_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, obj=checked_in_appointment
        )

    def test_returns_false_if_user_is_clinical_and_appointment_is_screened(
        self, clinical_user, screened_appointment
    ):
        assert not clinical_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, obj=screened_appointment
        )

    def test_returns_false_for_administrative_user(
        self, administrative_user, confirmed_appointment
    ):
        assert not administrative_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, confirmed_appointment
        )

    def test_returns_false_for_user_without_roles(self, confirmed_appointment):
        user_assignment = UserAssignmentFactory.create()
        user_assignment.make_current()

        assert not user_assignment.user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, confirmed_appointment
        )

    def test_returns_false_if_no_current_provider(self, confirmed_appointment):
        user_assignment = UserAssignmentFactory.create()

        assert not user_assignment.user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, confirmed_appointment
        )

    def test_returns_false_if_no_appointment_provided(self, clinical_user):
        assert not clinical_user.has_perm(Permission.START_MAMMOGRAM_APPOINTMENT)
