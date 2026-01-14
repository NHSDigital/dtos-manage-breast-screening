import pytest

from manage_breast_screening.mammograms.services.appointment_services import (
    ActionPerformedByDifferentUser,
    AppointmentStatusUpdater,
    InvalidStatus,
)
from manage_breast_screening.participants.models.appointment import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentStatusFactory,
)


@pytest.mark.django_db
class TestAppointmentStatusUpdater:
    def test_invalid_check_in(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(InvalidStatus):
            service.check_in()

    def test_valid_check_in(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.name == AppointmentStatus.CHECKED_IN

    def test_invalid_start(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(InvalidStatus):
            service.start()

    @pytest.mark.parametrize(
        "current_status", [AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN]
    )
    def test_valid_start(self, clinical_user, current_status):
        appointment = AppointmentFactory.create(current_status=current_status)
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.start()
        assert new_status.name == AppointmentStatus.STARTED

    def test_invalid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCREENED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(InvalidStatus):
            service.cancel()

    def test_valid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.cancel()
        assert new_status.name == AppointmentStatus.CANCELLED

    def test_invalid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(InvalidStatus):
            service.mark_did_not_attend()

    def test_valid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.mark_did_not_attend()
        assert new_status.name == AppointmentStatus.DID_NOT_ATTEND

    def test_invalid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(InvalidStatus):
            service.screen()

        with pytest.raises(InvalidStatus):
            service.screen(partial=True)

    def test_valid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.STARTED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.screen()
        assert new_status.name == AppointmentStatus.SCREENED

    def test_valid_partial_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.STARTED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.screen(partial=True)
        assert new_status.name == AppointmentStatus.PARTIALLY_SCREENED

    def test_check_in_is_idempotent(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCHEDULED
        )
        AppointmentStatusFactory.create(
            name=AppointmentStatus.CHECKED_IN,
            created_by=clinical_user,
            appointment=appointment,
        )
        assert appointment.current_status.name == AppointmentStatus.CHECKED_IN

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.name == AppointmentStatus.CHECKED_IN

    def test_cannot_start_appointment_started_by_someone_else(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.STARTED
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionPerformedByDifferentUser):
            service.start()
