import logging

from manage_breast_screening.participants.models.appointment import (
    AppointmentMachine,
    AppointmentStatusNames,
)

logger = logging.getLogger(__name__)


class ActionPerformedByDifferentUser(Exception):
    """
    The action has already been performed, but by a different user.
    """


class AppointmentStatusUpdater:
    """
    Transition an appointment to another status, assuming the user
    is permitted to perform the action.
    """

    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user
        self.machine = AppointmentMachine(
            start_value=self.appointment.current_status.name
        )

    @staticmethod
    def is_startable(appointment):
        return appointment is not None and appointment.current_status.name in (
            AppointmentStatusNames.SCHEDULED,
            AppointmentStatusNames.CHECKED_IN,
        )

    def check_in(self):
        if self.machine.current_state_value != AppointmentStatusNames.CHECKED_IN:
            self.machine.check_in()
        return self._save_to_appointment()

    def start(self):
        if self.machine.current_state_value != AppointmentStatusNames.IN_PROGRESS:
            self.machine.start()
        return self._save_to_appointment()

    def cancel(self):
        if self.machine.current_state_value != AppointmentStatusNames.CANCELLED:
            self.machine.cancel()
        return self._save_to_appointment()

    def mark_did_not_attend(self):
        if self.machine.current_state_value != AppointmentStatusNames.DID_NOT_ATTEND:
            self.machine.mark_did_not_attend()
        return self._save_to_appointment()

    def screen(self, partial=False):
        if (
            partial
            and self.machine.current_state_value
            != AppointmentStatusNames.PARTIALLY_SCREENED
        ):
            self.machine.partial_screen()
        elif self.machine.current_state_value != AppointmentStatusNames.SCREENED:
            self.machine.screen()

        return self._save_to_appointment()

    def _save_to_appointment(self):
        """
        Make operations idempotent, providing that we're not changing
        the created_by user.
        """
        new_status, created = self.appointment.statuses.get_or_create(
            name=self.machine.current_state_value,
            defaults=dict(created_by=self.current_user),
        )

        if not created and new_status.created_by != self.current_user:
            logger.warning(
                f"Current status is already {new_status}, and was set by a different user"
            )
            raise ActionPerformedByDifferentUser(new_status)

        return new_status
