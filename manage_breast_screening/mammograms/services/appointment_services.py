import logging

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.mammograms.services.appointment_state_machine import (
    AppointmentStateMachine,
)
from manage_breast_screening.participants.models.appointment import AppointmentStatus

logger = logging.getLogger(__name__)


class ActionNotPermitted(Exception):
    """
    The user doesn't have permission to perform the action.
    """


class ActionPerformedByDifferentUser(Exception):
    """
    The action has already been performed, but by a different user.
    """


class AppointmentStatusUpdater:
    """
    Transition an appointment to another status.
    """

    def __init__(self, appointment, current_user):
        if appointment is None:
            raise ValueError

        self.appointment = appointment
        self.current_user = current_user

        current_status = appointment.current_status
        self.state_machine = AppointmentStateMachine(
            current_status.name,
            identity_check_invalid=current_status.created_by != current_user,
        )

    def check_in(self):
        current_status = self._get_existing_status(AppointmentStatus.CHECKED_IN)
        if current_status:
            return current_status

        return self._append_status(self.state_machine.check_in())

    @staticmethod
    def can_be_started(appointment):
        return appointment is not None and appointment.current_status.name in (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CHECKED_IN,
        )

    def start(self):
        if not self.current_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, obj=self.appointment
        ):
            raise ActionNotPermitted(self.appointment.current_status)

        current_status = self._get_existing_status(AppointmentStatus.STARTED)
        if current_status:
            return current_status

        return self._append_status(self.state_machine.start())

    def cancel(self):
        current_status = self._get_existing_status(AppointmentStatus.CANCELLED)
        if current_status:
            return current_status

        return self._append_status(self.state_machine.cancel())

    def mark_did_not_attend(self):
        current_status = self._get_existing_status(AppointmentStatus.DID_NOT_ATTEND)
        if current_status:
            return current_status

        return self._append_status(self.state_machine.mark_did_not_attend())

    def screen(self, partial=False):
        current_status = self._get_existing_status(AppointmentStatus.SCREENED)
        if current_status:
            return current_status

        return self._append_status(self.state_machine.screen(partial=partial))

    def _get_existing_status(self, status):
        """
        Check if we're already in the status. If so, and if the status was
        created by the current user, return that, so as to make operations
        idempotent.
        """
        current_status = self.appointment.current_status
        if current_status.name == status:
            if current_status.created_by == self.current_user:
                return current_status
            else:
                logger.warning(
                    f"Current status is already {status}, and was set by a different user"
                )
                raise ActionPerformedByDifferentUser(status)

    def _append_status(self, status):
        return self.appointment.statuses.create(
            name=status,
            created_by=self.current_user,
        )
