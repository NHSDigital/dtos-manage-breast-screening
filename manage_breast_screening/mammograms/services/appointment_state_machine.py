import logging

from manage_breast_screening.participants.models.appointment import AppointmentStatus

logger = logging.getLogger(__name__)


class InvalidStatus(Exception):
    """
    The appointment is not in a valid status to perform the action.
    """


class AppointmentStateMachine:
    """
    State machine for appointment statuses.
    This ignores persistance, and permissions, which should be handled at the view level.
    """

    def __init__(self, state, identity_check_invalid=False):
        """
        :param state: The name of the current status
        :param identity_check_invalid: Whether we should consider previous identity checks as invalid
               because they weren't done by the current user
        """
        self.state = state
        self.identity_check_invalid = identity_check_invalid

    def can_check_in(self):
        return self.state == AppointmentStatus.SCHEDULED

    def can_cancel(self):
        return self.state == AppointmentStatus.SCHEDULED

    def can_mark_did_not_attend(self):
        return self.state == AppointmentStatus.SCHEDULED

    def can_start(self):
        return self.state in (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CHECKED_IN,
        )

    def can_confirm_identity(self):
        return (self.state == AppointmentStatus.STARTED) or (
            self.state == AppointmentStatus.PAUSED and self.identity_check_invalid
        )

    def can_review_medical_information(self):
        return (
            self.state == AppointmentStatus.IDENTITY_CONFIRMED
            and not self.identity_check_invalid
        )

    def can_take_images(self):
        return (
            self.state == AppointmentStatus.MEDICAL_INFORMATION_REVIEWED
            and not self.identity_check_invalid
        )

    def can_screen(self):
        return (
            self.state == AppointmentStatus.IMAGES_TAKEN
            and not self.identity_check_invalid
        )

    def can_pause(self):
        return (
            self.state in AppointmentStatus.IN_PROGRESS_STATUSES
            and not self.identity_check_invalid
        )

    def can_resume(self):
        return self.state == AppointmentStatus.PAUSED

    def can_mark_attended_not_screened(self):
        return (
            self.state in AppointmentStatus.IN_PROGRESS_STATUSES
            and not self.identity_check_invalid
        )

    def check_in(self):
        return self._transition(AppointmentStatus.CHECKED_IN, self.can_check_in)

    def cancel(self):
        return self._transition(AppointmentStatus.CANCELLED, self.can_cancel)

    def mark_did_not_attend(self):
        return self._transition(
            AppointmentStatus.DID_NOT_ATTEND, self.can_mark_did_not_attend
        )

    def start(self):
        return self._transition(AppointmentStatus.STARTED, self.can_start)

    def confirm_identity(self):
        self._transition(
            AppointmentStatus.IDENTITY_CONFIRMED, self.can_confirm_identity
        )

        self.identity_check_invalid = False

        return self.state

    def review_medical_information(self):
        return self._transition(
            AppointmentStatus.MEDICAL_INFORMATION_REVIEWED,
            self.can_review_medical_information,
        )

    def take_images(self):
        return self._transition(AppointmentStatus.IMAGES_TAKEN, self.can_take_images)

    def screen(self, partial=False):
        name = (
            AppointmentStatus.PARTIALLY_SCREENED
            if partial
            else AppointmentStatus.SCREENED
        )

        return self._transition(name, self.can_screen)

    def pause(self):
        return self._transition(AppointmentStatus.PAUSED, self.can_pause)

    def resume(self):
        to_state = (
            AppointmentStatus.TAKEN_OVER
            if self.identity_check_invalid
            else AppointmentStatus.RESUMED
        )
        return self._transition(to_state, self.can_resume)

    def _transition(self, to_state, condition):
        if not condition():
            raise InvalidStatus(to_state)
        else:
            self.state = to_state

        return self.state
