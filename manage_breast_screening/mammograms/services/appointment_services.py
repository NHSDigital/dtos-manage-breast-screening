import logging

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.participants.models.appointment import AppointmentStatus

logger = logging.getLogger(__name__)


class ActionNotPermitted(Exception):
    """
    The user doesn't have permission to perform the action.
    """


class InvalidStatus(Exception):
    """
    The appointment is not in a valid status to perform the action.
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
        self.appointment = appointment
        self.current_user = current_user

    def check_in(self):
        return self._transition(
            to_status=AppointmentStatus.CHECKED_IN,
            from_statuses=(AppointmentStatus.SCHEDULED,),
        )

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

        return self._transition(
            to_status=AppointmentStatus.STARTED,
            from_statuses=(AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN),
        )

    def cancel(self):
        return self._transition(
            to_status=AppointmentStatus.CANCELLED,
            from_statuses=(AppointmentStatus.SCHEDULED,),
        )

    def mark_did_not_attend(self):
        return self._transition(
            to_status=AppointmentStatus.DID_NOT_ATTEND,
            from_statuses=(AppointmentStatus.SCHEDULED,),
        )

    def screen(self, partial=False):
        return self._transition(
            to_status=(
                AppointmentStatus.PARTIALLY_SCREENED
                if partial
                else AppointmentStatus.SCREENED
            ),
            from_statuses=(AppointmentStatus.STARTED,),
        )

    def _transition(self, to_status, from_statuses):
        current_status = self.appointment.current_status.name
        if current_status != to_status and current_status not in from_statuses:
            raise InvalidStatus(self.appointment.current_status)

        return self._get_or_create(status=to_status)

    def _get_or_create(self, status):
        """
        Make operations idempotent, providing that we're not changing
        the created_by user.
        """
        new_status, created = self.appointment.statuses.get_or_create(
            name=status,
            defaults=dict(created_by=self.current_user),
        )

        if not created and new_status.created_by != self.current_user:
            logger.warning(
                f"Current status is already {new_status}, and was set by a different user"
            )
            raise ActionPerformedByDifferentUser(new_status)

        return new_status
