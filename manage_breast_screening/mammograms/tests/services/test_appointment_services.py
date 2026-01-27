import pytest
from statemachine.exceptions import TransitionNotAllowed

from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.participants.models.appointment import (
    ActionPerformedByDifferentUser,
    AppointmentMachine,
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentStatusFactory,
)


@pytest.mark.django_db
class TestAppointmentStatusUpdater:
    def test_invalid_check_in(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.check_in()

    def test_valid_check_in(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.name == AppointmentStatusNames.CHECKED_IN

    def test_invalid_start(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.start()

    @pytest.mark.parametrize(
        "current_status",
        [AppointmentStatusNames.SCHEDULED, AppointmentStatusNames.CHECKED_IN],
    )
    def test_valid_start(self, clinical_user, current_status):
        appointment = AppointmentFactory.create(current_status=current_status)
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.start()
        assert new_status.name == AppointmentStatusNames.IN_PROGRESS

    def test_invalid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCREENED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.cancel()

    def test_valid_cancel(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.cancel()
        assert new_status.name == AppointmentStatusNames.CANCELLED

    def test_invalid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.mark_did_not_attend()

    def test_valid_mark_did_not_attend(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.mark_did_not_attend()
        assert new_status.name == AppointmentStatusNames.DID_NOT_ATTEND

    def test_valid_mark_attended_not_screened(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.mark_attended_not_screened()
        assert new_status.name == AppointmentStatusNames.ATTENDED_NOT_SCREENED

    def test_invalid_mark_attended_not_screened(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCREENED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.mark_attended_not_screened()

    def test_invalid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CANCELLED
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.screen()

        with pytest.raises(TransitionNotAllowed):
            service.partial_screen()

    def test_valid_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.screen()
        assert new_status.name == AppointmentStatusNames.SCREENED

    def test_valid_partial_screen(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )
        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.partial_screen()
        assert new_status.name == AppointmentStatusNames.PARTIALLY_SCREENED

    def test_check_in_is_idempotent(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentStatusFactory.create(
            name=AppointmentStatusNames.CHECKED_IN,
            created_by=clinical_user,
            appointment=appointment,
        )
        assert appointment.current_status.name == AppointmentStatusNames.CHECKED_IN

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.check_in()
        assert new_status.name == AppointmentStatusNames.CHECKED_IN

    def test_cannot_start_appointment_started_by_someone_else(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(ActionPerformedByDifferentUser):
            service.start()

    def test_can_resume_an_appointment_paused_by_someone_else(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )

        AppointmentStatusFactory.create(
            name=AppointmentStatusNames.PAUSED,
            created_by=clinical_user,
            appointment=appointment,
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.resume()
        assert new_status.name == AppointmentStatusNames.IN_PROGRESS

    def test_can_pause_an_appointment(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        new_status = service.pause()
        assert new_status.name == AppointmentStatusNames.PAUSED

    def test_invalid_pause(self, clinical_user):
        appointment = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentStatusFactory.create(
            name=AppointmentStatusNames.CANCELLED,
            created_by=clinical_user,
            appointment=appointment,
        )

        service = AppointmentStatusUpdater(
            appointment=appointment, current_user=clinical_user
        )

        with pytest.raises(TransitionNotAllowed):
            service.pause()

    def test_class_has_methods_for_each_event(self):
        for event in AppointmentMachine().events:
            assert hasattr(AppointmentStatusUpdater, event), f"missing {event}() method"
