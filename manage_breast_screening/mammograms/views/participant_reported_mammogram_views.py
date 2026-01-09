import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.participants.forms import ParticipantReportedMammogramForm
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.services import fetch_most_recent_provider
from manage_breast_screening.participants.views import parse_return_url

from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class ParticipantReportedMammogramMixin(InProgressAppointmentMixin):
    form_class = ParticipantReportedMammogramForm
    template_name = "mammograms/add_previous_mammogram.jinja"
    thing_name = "a previous mammogram"
    within_six_months = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        kwargs["most_recent_provider"] = fetch_most_recent_provider(self.participant.pk)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": {
                    "href": self.get_success_url(),
                },
                "caption": participant.full_name,
                "return_url": self.request.GET.get("return_url", ""),
            },
        )

        return context

    def form_valid(self, form):
        exact_date = form.cleaned_data.get("exact_date")
        self.within_six_months = (
            exact_date and exact_date > date.today() - relativedelta(months=6)
        )
        self.form = form

        return super().form_valid(form)

    def should_add_message(self, form) -> bool:
        return not self.within_six_months

    def get_success_url(self):
        return_url = parse_return_url(
            self.request,
            default=reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            ),
        )

        if self.within_six_months:
            return (
                reverse(
                    "mammograms:appointment_should_not_proceed",
                    kwargs={
                        "appointment_pk": self.appointment.pk,
                        "participant_reported_mammogram_pk": self.form.participant_reported_mammogram_pk,
                    },
                )
                + f"?return_url={return_url}"
            )
        else:
            return return_url


class AddParticipantReportedMammogramView(
    ParticipantReportedMammogramMixin, AddWithAuditView
):
    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateParticipantReportedMammogramView(
    ParticipantReportedMammogramMixin, UpdateWithAuditView
):
    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def confirm_delete_link_text(self, thing_name):
        return "Delete this mammogram"

    def get_object(self):
        try:
            return ParticipantReportedMammogram.objects.get(
                pk=self.kwargs["participant_reported_mammogram_pk"],
            )
        except ParticipantReportedMammogram.DoesNotExist:
            logger.exception(
                "Participant reported mammogram does not exist for kwargs=%s",
                self.kwargs,
            )
            return None

    def get_delete_url(self):
        return (
            reverse(
                "mammograms:delete_previous_mammogram",
                kwargs={
                    "pk": self.kwargs["pk"],
                    "participant_reported_mammogram_pk": self.kwargs[
                        "participant_reported_mammogram_pk"
                    ],
                },
            )
            + f"?return_url={self.request.GET.get('return_url', '')}"
        )


class DeleteParticipantReportedMammogramView(
    InProgressAppointmentMixin, DeleteWithAuditView
):
    def get_thing_name(self, object):
        return "item"

    def get_success_message_content(self, object):
        return "Deleted other procedure"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.participant.reported_mammograms.get(
            pk=self.kwargs["participant_reported_mammogram_pk"]
        )

    def get_success_url(self) -> str:
        return parse_return_url(
            self.request,
            default=reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            ),
        )
