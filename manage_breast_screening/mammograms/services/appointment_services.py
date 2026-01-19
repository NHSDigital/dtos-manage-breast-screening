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


class AppointmentStateMachine:
    """
    State machine for appointment statuses.
    This ignores persistance, which must be handled separately.
    """

    @classmethod
    def from_appointment(cls, appointment):
        if appointment is None:
            raise ValueError

        return cls(appointment.current_status)

    def __init__(self, current_status):
        self.status = current_status

    def can_check_in(self):
        return self.status.name == AppointmentStatus.SCHEDULED

    def can_cancel(self):
        return self.status.name == AppointmentStatus.SCHEDULED

    def can_mark_did_not_attend(self):
        return self.status.name == AppointmentStatus.SCHEDULED

    def can_start(self):
        return self.status.name in (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CHECKED_IN,
        )

    def can_confirm_identity(self, user):
        return (self.status.name == AppointmentStatus.STARTED) or (
            self.status.name == AppointmentStatus.PAUSED
            and self.status.created_by != user
        )

    def can_review_medical_information(self, user):
        return (
            self.status.created_by == user
            and self.status.name == AppointmentStatus.IDENTITY_CONFIRMED
        )

    def can_take_images(self, user):
        return (
            self.status.created_by == user
            and self.status.name == AppointmentStatus.MEDICAL_INFORMATION_REVIEWED
        )

    def can_screen(self, user):
        return (
            self.status.created_by == user
            and self.status.name == AppointmentStatus.IMAGES_TAKEN
        )

    def can_pause(self, user):
        return (
            self.status.created_by == user
            and self.status.name in AppointmentStatus.IN_PROGRESS_STATUSES
        )

    def can_mark_attended_not_screened(self, user):
        return (
            self.status.created_by == user
            and self.status.name in AppointmentStatus.IN_PROGRESS_STATUSES
        )

    def check_in(self, user):
        if not self.can_check_in():
            raise ActionNotPermitted(AppointmentStatus.CHECKED_IN)

        self.status = AppointmentStatus(
            name=AppointmentStatus.CHECKED_IN, created_by=user
        )

    def start(self, user):
        if not self.can_start():
            raise ActionNotPermitted(AppointmentStatus.STARTED)

        self.status = AppointmentStatus(name=AppointmentStatus.STARTED, created_by=user)

    def cancel(self, user):
        if not self.can_cancel():
            raise ActionNotPermitted(AppointmentStatus.CANCELLED)

        self.status = AppointmentStatus(
            name=AppointmentStatus.CHECKED_IN, created_by=user
        )

    def mark_did_not_attend(self, user):
        if not self.can_mark_did_not_attend():
            raise ActionNotPermitted(AppointmentStatus.DID_NOT_ATTEND)

        self.status = AppointmentStatus(
            name=AppointmentStatus.DID_NOT_ATTEND, created_by=user
        )

    def screen(self, user, partial=False):
        name = (
            AppointmentStatus.PARTIALLY_SCREENED
            if partial
            else AppointmentStatus.SCREENED
        )
        if not self.can_screen(user):
            raise ActionNotPermitted(name)

        self.status = AppointmentStatus(name=name, created_by=user)


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
