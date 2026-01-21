import logging

from manage_breast_screening.participants.models.appointment import (
    AppointmentMachine,
    AppointmentStatusNames,
)

logger = logging.getLogger(__name__)


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

    def check_in(self):
        if self.machine.current_state_value != AppointmentStatusNames.CHECKED_IN:
            self.machine.check_in()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def start(self):
        if self.machine.current_state_value != AppointmentStatusNames.IN_PROGRESS:
            self.machine.start()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def cancel(self):
        if self.machine.current_state_value != AppointmentStatusNames.CANCELLED:
            self.machine.cancel()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def mark_did_not_attend(self):
        if self.machine.current_state_value != AppointmentStatusNames.DID_NOT_ATTEND:
            self.machine.mark_did_not_attend()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def screen(self, partial=False):
        if (
            partial
            and self.machine.current_state_value
            != AppointmentStatusNames.PARTIALLY_SCREENED
        ):
            self.machine.partial_screen()
        elif self.machine.current_state_value != AppointmentStatusNames.SCREENED:
            self.machine.screen()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )
