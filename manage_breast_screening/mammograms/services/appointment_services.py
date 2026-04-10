import logging

from manage_breast_screening.participants.models.appointment import (
    ActionPerformedByDifferentUser,
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

    def _transition(self, event_name, target_status):
        appointment = self.appointment

        if appointment.status == target_status:
            # Already in the target status — idempotent, but check user
            if appointment.status_changed_by != self.current_user:
                raise ActionPerformedByDifferentUser(target_status)
            return

        # Fire the state machine event — this validates the transition
        # and updates sm.current_state
        getattr(appointment, event_name)()

        # Now persist the new state
        appointment.status = target_status
        appointment.status_changed_by = self.current_user
        appointment.save(update_fields=["status", "status_changed_by", "updated_at"])

    def check_in(self):
        self._transition("check_in", AppointmentStatusNames.CHECKED_IN)

    def start(self):
        self._transition("start", AppointmentStatusNames.IN_PROGRESS)

    def cancel(self):
        self._transition("cancel", AppointmentStatusNames.CANCELLED)

    def mark_did_not_attend(self):
        self._transition("mark_did_not_attend", AppointmentStatusNames.DID_NOT_ATTEND)

    def mark_attended_not_screened(self):
        self._transition(
            "mark_attended_not_screened", AppointmentStatusNames.ATTENDED_NOT_SCREENED
        )

    def partial_screen(self):
        self._transition("partial_screen", AppointmentStatusNames.PARTIALLY_SCREENED)

    def screen(self):
        self._transition("screen", AppointmentStatusNames.SCREENED)

    def pause(self):
        self._transition("pause", AppointmentStatusNames.PAUSED)

    def resume(self):
        self._transition("resume", AppointmentStatusNames.IN_PROGRESS)


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
        result = self.appointment.completed_workflow_steps.filter(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=self.current_user,
        ).exists()

        logger.info(f"Checking identity confirmed for {self.current_user.pk}: {result}")

        return result

    def get_completed_steps(self):
        step_names = set(
            self.appointment.completed_workflow_steps.values_list(
                "step_name", flat=True
            ).distinct()
        )

        logger.info(f"Completed steps for {self.current_user.pk}: {step_names}")

        return step_names
