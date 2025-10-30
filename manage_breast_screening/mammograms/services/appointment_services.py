import logging

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.participants.models.appointment import AppointmentStatus

logger = logging.getLogger(__name__)


class ActionNotPermitted(Exception):
    """
    The user doesn't have permission to perform the action.
    """


class AppointmentStatusUpdater:
    """
    Transition an appointment to another state.
    Each state is logged in AppointmentStatusHistory and associated with a user.
    """

    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user

    def check_in(self):
        return self._transition(
            to_state=AppointmentStatus.CHECKED_IN,
            from_states=(AppointmentStatus.CONFIRMED,),
        )

    @staticmethod
    def is_startable(appointment):
        return appointment is not None and appointment.current_status.state in (
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
        )

    def start(self):
        if not self.current_user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, obj=self.appointment
        ):
            raise ActionNotPermitted(self.appointment.current_status)

        return self._transition(
            to_state=AppointmentStatus.IN_PROGRESS,
            from_states=(AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN),
        )

    def cancel(self):
        return self._transition(
            to_state=AppointmentStatus.CANCELLED,
            from_states=(AppointmentStatus.CONFIRMED,),
        )

    def mark_did_not_attend(self):
        return self._transition(
            to_state=AppointmentStatus.DID_NOT_ATTEND,
            from_states=(AppointmentStatus.CONFIRMED,),
        )

    def screen(self, partial=False):
        return self._transition(
            to_state=(
                AppointmentStatus.PARTIALLY_SCREENED
                if partial
                else AppointmentStatus.SCREENED
            ),
            from_states=(AppointmentStatus.IN_PROGRESS,),
        )

    def _transition(self, to_state, from_states):
        current_state = self.appointment.current_status.state
        if current_state != to_state and current_state not in from_states:
            raise ActionNotPermitted(self.appointment.current_status)

        return self._get_or_create(state=to_state)

    def _get_or_create(self, state):
        """
        Make operations idempotent, providing that we're not changing
        the created_by user.
        """
        new_status, created = self.appointment.statuses.get_or_create(
            state=state,
            defaults=dict(created_by=self.current_user),
        )

        if not created and new_status.created_by != self.current_user:
            logger.warning(
                f"Current status is already {new_status}, and was set by a different user"
            )
            raise ActionNotPermitted(new_status)

        return new_status
