from functools import cached_property

from django.urls import reverse

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.participants.models.appointment import (
    AppointmentMachine,
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
)

from ...core.utils.date_formatting import format_date, format_relative_date, format_time
from ...participants.models import AppointmentNote, AppointmentStatus, SupportReasons
from ...participants.presenters import ParticipantPresenter, status_colour


class AppointmentPresenter:
    def __init__(self, appointment, tab_description="Appointment details"):
        self._appointment = appointment
        self.tab_description = tab_description

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
    def page_title(self):
        return f"{self.caption}: {self.tab_description}"

    @cached_property
    def start_time(self):
        return self.clinic_slot.starts_at

    def workflow_steps(self, active_workflow_step):
        completed_workflow_steps = (
            self._appointment.completed_workflow_steps.values_list(
                "step_name", flat=True
            )
        )

        steps = []

        all_previous_steps_completed = True
        for i, step in enumerate(AppointmentWorkflowStepCompletion.StepNames):
            is_completed = step.name in completed_workflow_steps
            is_current = step.name == active_workflow_step
            is_disabled = not (
                all_previous_steps_completed or is_completed or is_current
            )
            all_previous_steps_completed = all_previous_steps_completed and is_completed

            classes = "app-workflow-side-nav__item"
            if is_current:
                classes += " app-workflow-side-nav__item--current"
            if is_completed:
                classes += " app-workflow-side-nav__item--completed"
            if is_disabled:
                classes += " app-workflow-side-nav__item--disabled"

            match step:
                case AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY:
                    view_name = "confirm_identity"
                case AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION:
                    view_name = "record_medical_information"
                case AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES:
                    view_name = "take_images"
                case AppointmentWorkflowStepCompletion.StepNames.CHECK_INFORMATION:
                    view_name = "check_information"

            steps.append(
                {
                    "label": step.label,
                    "completed": is_completed,
                    "current": is_current,
                    "disabled": is_disabled,
                    "classes": classes,
                    "url": reverse(
                        "mammograms:" + view_name,
                        kwargs={
                            "pk": self._appointment.pk,
                        },
                    ),
                }
            )

        return steps

    @cached_property
    def has_appointment_note(self):
        return hasattr(self._appointment, "note")

    @cached_property
    def is_special_appointment(self):
        return bool(self.participant.extra_needs)

    @cached_property
    def can_be_made_special(self):
        return not self.is_special_appointment and self._appointment.active

    @cached_property
    def can_be_checked_in(self):
        return AppointmentMachine.from_appointment(self._appointment).can("check_in")

    @cached_property
    def active(self):
        return self._appointment.active

    def can_be_started_by(self, user):
        return user.has_perm(
            Permission.DO_MAMMOGRAM_APPOINTMENT, self._appointment
        ) and AppointmentMachine.from_appointment(self._appointment).can("start")

    def can_be_resumed_by(self, user):
        if not user.has_perm(Permission.DO_MAMMOGRAM_APPOINTMENT, self._appointment):
            return False

        # Allow the same user to return to an appointment they have in progress
        # This will only happen if there is a technical problem and the
        # user loses their browsing context.
        return AppointmentMachine.from_appointment(self._appointment).can(
            "resume"
        ) or self._appointment.current_status.is_in_progress_with(user)

    @cached_property
    def special_appointment_tag_properties(self):
        return {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-top-2",
            "text": "Special appointment",
        }

    @cached_property
    def appointment_note_tag_properties(self):
        return {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-top-2",
            "text": "Appointment note",
        }

    @cached_property
    def current_status(self):
        current_status = self._appointment.current_status
        colour = status_colour(current_status)
        display_text = current_status.get_name_display()

        return {
            "classes": (
                f"nhsuk-tag--{colour} app-u-nowrap" if colour else "app-u-nowrap"
            ),
            "text": display_text,
            "key": current_status.name,
            "is_confirmed": current_status.name == AppointmentStatusNames.SCHEDULED,
            "is_screened": current_status.name == AppointmentStatusNames.SCREENED,
        }

    @cached_property
    def status_attribution(self):
        if self._appointment.current_status.is_in_progress():
            return (
                "with " + self._appointment.current_status.created_by.get_short_name()
            )
        elif self._appointment.current_status.is_final_status():
            return "by " + self._appointment.current_status.created_by.get_short_name()
        else:
            return None

    def attribution_user_check(self, user):
        if user.pk == self._appointment.current_status.created_by.pk:
            return " (you)"
        else:
            return ""

    @cached_property
    def note(self):
        try:
            return self._appointment.note
        except AppointmentNote.DoesNotExist:
            return None

    @cached_property
    def status_bar(self):
        return StatusBarPresenter(self)


class StatusBarPresenter:
    def __init__(self, appointment):
        self.appointment = appointment
        self.clinic_slot = appointment.clinic_slot
        self.participant = appointment.participant

    def show_status_bar_for(self, user):
        # The appointment status bar should only display if the current user is the one that has the appointment 'in progress'
        current_status = self.appointment._appointment.current_status
        return (
            current_status.is_in_progress()
            and user.nhs_uid == current_status.created_by.nhs_uid
        )

    @property
    def tag_properties(self):
        return {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-left-1",
            "text": "Special appointment",
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

        return f"{format_date(clinic.starts_at)} ({format_relative_date(clinic.starts_at)}) \n {format_time(clinic_slot.starts_at)} ({clinic_slot.duration_in_minutes} minutes)"

    @cached_property
    def clinic_date_and_slot_time(self):
        clinic_slot = self._clinic_slot
        clinic = self._clinic

        return (
            f"{format_date(clinic.starts_at)} at {format_time(clinic_slot.starts_at)}"
        )

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


class ImagesTakenPresenter:
    def __init__(self, appointment):
        study = appointment.study
        self.additional_details = study.additional_details

        self.total_count = 0
        self.views_taken = {}
        for view, count in study.series_counts().items():
            image_name = view.short_name
            self.views_taken[image_name] = count
            self.total_count += count

    @property
    def title(self):
        if self.total_count == 0:
            return "No images taken"
        elif self.total_count == 1:
            return "1 image taken"
        else:
            return f"{self.total_count} images taken"
