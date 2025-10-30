import pytest

from manage_breast_screening.mammograms.services.appointment_services import (
    ActionNotPermitted,
    AppointmentStatusUpdater,
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

        with pytest.raises(ActionNotPermitted):
            service.check_in()

    def test_valid_check_in(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CONFIRMED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.state == AppointmentStatus.CHECKED_IN

    def test_invalid_start(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionNotPermitted):
            service.start()

    @pytest.mark.parametrize(
        "current_status", [AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN]
    )
    def test_valid_start(self, clinical_user, current_status):
        appointment = AppointmentFactory.create(current_status=current_status)
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.start()
        assert new_status.state == AppointmentStatus.IN_PROGRESS

    def test_invalid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.SCREENED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionNotPermitted):
            service.cancel()

    def test_valid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CONFIRMED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.cancel()
        assert new_status.state == AppointmentStatus.CANCELLED

    def test_invalid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionNotPermitted):
            service.mark_did_not_attend()

    def test_valid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CONFIRMED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.mark_did_not_attend()
        assert new_status.state == AppointmentStatus.DID_NOT_ATTEND

    def test_invalid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionNotPermitted):
            service.screen()

        with pytest.raises(ActionNotPermitted):
            service.screen(partial=True)

    def test_valid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.IN_PROGRESS
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.screen()
        assert new_status.state == AppointmentStatus.SCREENED

    def test_valid_partial_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.IN_PROGRESS
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.screen(partial=True)
        assert new_status.state == AppointmentStatus.PARTIALLY_SCREENED

    def test_check_in_is_idempotent(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.CONFIRMED
        )
        AppointmentStatusFactory.create(
            state=AppointmentStatus.CHECKED_IN,
            created_by=clinical_user,
            appointment=appointment,
        )
        assert appointment.current_status.state == AppointmentStatus.CHECKED_IN

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.state == AppointmentStatus.CHECKED_IN

    def test_cannot_start_appointment_started_by_someone_else(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatus.IN_PROGRESS
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionNotPermitted):
            service.start()
