import logging

from manage_breast_screening.participants.models.appointment import (
    AppointmentMachine,
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
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

    def mark_attended_not_screened(self):
        if (
            self.machine.current_state_value
            != AppointmentStatusNames.ATTENDED_NOT_SCREENED
        ):
            self.machine.mark_attended_not_screened()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def partial_screen(self):
        if (
            self.machine.current_state_value
            != AppointmentStatusNames.PARTIALLY_SCREENED
        ):
            self.machine.partial_screen()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def screen(self):
        if self.machine.current_state_value != AppointmentStatusNames.SCREENED:
            self.machine.screen()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def pause(self):
        if self.machine.current_state_value != AppointmentStatusNames.SCREENED:
            self.machine.pause()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )

    def resume(self):
        self.machine.resume()

        return self.appointment.set_status(
            self.machine.current_state_value, created_by=self.current_user
        )


class RecallService:
    """
    Mark that a user needs to be recalled back for any reason.
    """

    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user

    def reinvite(self):
        # Currently this is just a boolean flag; when we implement appointment
        # scheduling then this will need to store the reason for the reinvite.
        self.appointment.reinvite = True
        self.appointment.save()


class AppointmentWorkflowService:
    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user

    def is_identity_confirmed_by_user(self):
        return self.appointment.completed_workflow_steps.filter(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=self.current_user,
        ).exists()

    def get_completed_steps(self):
        return set(
            self.appointment.completed_workflow_steps.values_list(
                "step_name", flat=True
            ).distinct()
        )
