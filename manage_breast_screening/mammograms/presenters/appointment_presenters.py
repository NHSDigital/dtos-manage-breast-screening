from functools import cached_property

from django.urls import reverse

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)

from ...core.utils.date_formatting import format_date, format_relative_date, format_time
from ...participants.models import AppointmentStatus, SupportReasons
from ...participants.presenters import ParticipantPresenter, status_colour


class AppointmentPresenter:
    def __init__(self, appointment):
        self._appointment = appointment

        self.allStatuses = AppointmentStatus
        self.pk = appointment.pk
        self.clinic_slot = ClinicSlotPresenter(appointment.clinic_slot)
        self.participant = ParticipantPresenter(
            appointment.screening_episode.participant
        )
        self.screening_protocol = appointment.screening_episode.get_protocol_display()

        self.special_appointment = (
            SpecialAppointmentPresenter(self.participant.extra_needs, self.pk)
            if self.is_special_appointment
            else None
        )

    @cached_property
    def participant_url(self):
        return self.participant.url

    @cached_property
    def clinic_url(self):
        return self.clinic_slot.clinic_url

    @cached_property
    def special_appointment_url(self):
        return reverse(
            "mammograms:provide_special_appointment_details",
            kwargs={"pk": self._appointment.pk},
        )

    @cached_property
    def caption(self):
        return f"{self.clinic_slot.clinic_type} appointment"

    @cached_property
    def start_time(self):
        return self.clinic_slot.starts_at

    @cached_property
    def is_special_appointment(self):
        return bool(self.participant.extra_needs)

    @cached_property
    def can_be_made_special(self):
        return not self.is_special_appointment and self._appointment.active

    @cached_property
    def can_be_checked_in(self):
        return self._appointment.current_status.state == AppointmentStatus.CONFIRMED

    @cached_property
    def active(self):
        return self._appointment.active

    def can_be_started_by(self, user):
        return user.has_perm(
            Permission.START_MAMMOGRAM_APPOINTMENT, self._appointment
        ) and AppointmentStatusUpdater.is_startable(self._appointment)

    @cached_property
    def special_appointment_tag_properties(self):
        return {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-top-2",
            "text": "Special appointment",
        }

    @cached_property
    def current_status(self):
        current_status = self._appointment.current_status

        colour = status_colour(current_status.state)

        return {
            "classes": f"nhsuk-tag--{colour} app-u-nowrap"
            if colour
            else "app-u-nowrap",
            "text": current_status.get_state_display(),
            "key": current_status.state,
            "is_confirmed": current_status.state == AppointmentStatus.CONFIRMED,
            "is_screened": current_status.state == AppointmentStatus.SCREENED,
        }


class ClinicSlotPresenter:
    def __init__(self, clinic_slot):
        self._clinic_slot = clinic_slot
        self._clinic = clinic_slot.clinic

        self.clinic_id = self._clinic.id

    @cached_property
    def clinic_type(self):
        return self._clinic.get_type_display().capitalize()

    @cached_property
    def clinic_url(self):
        return reverse("clinics:show", kwargs={"pk": self._clinic.pk})

    @cached_property
    def slot_time_and_clinic_date(self):
        clinic_slot = self._clinic_slot
        clinic = self._clinic

        return f"{format_time(clinic_slot.starts_at)} ({clinic_slot.duration_in_minutes} minutes) - {format_date(clinic.starts_at)} ({format_relative_date(clinic.starts_at)})"

    @cached_property
    def starts_at(self):
        return format_time(self._clinic_slot.starts_at)


class SpecialAppointmentPresenter:
    def __init__(self, extra_needs, appointment_pk):
        self._extra_needs = extra_needs
        self._appointment_pk = appointment_pk

    @cached_property
    def reasons(self):
        result = []
        for reason, reason_details in self._extra_needs.items():
            result.append(
                {
                    "label": SupportReasons[reason].label,
                    "temporary": reason_details.get("temporary"),
                    "details": reason_details.get("details"),
                }
            )
        return result

    @cached_property
    def change_url(self):
        return reverse(
            "mammograms:provide_special_appointment_details",
            kwargs={"pk": self._appointment_pk},
        )
