import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.core.views.generic import DeleteWithAuditView
from manage_breast_screening.participants.models import AppointmentNote

from ..forms import AppointmentNoteForm
from ..presenters import AppointmentPresenter, present_secondary_nav
from .mixins import AppointmentMixin

logger = logging.getLogger(__name__)


class AppointmentNoteView(AppointmentMixin, FormView):
    template_name = "mammograms/show/appointment_note.jinja"
    form_class = AppointmentNoteForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.appointment
        appointment_presenter = AppointmentPresenter(
            appointment, tab_description="Note"
        )

        context.update(
            {
                "heading": appointment_presenter.participant.full_name,
                "caption": appointment_presenter.caption,
                "page_title": appointment_presenter.page_title,
                "presented_appointment": appointment_presenter,
                "secondary_nav_items": present_secondary_nav(
                    appointment.pk, current_tab="note"
                ),
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs["instance"] = self.appointment.note
        except AppointmentNote.DoesNotExist:
            kwargs["instance"] = AppointmentNote(appointment=self.appointment)
        return kwargs

    def form_valid(self, form):
        is_new_note = form.instance._state.adding
        note = form.save()
        auditor = Auditor.from_request(self.request)
        if is_new_note:
            auditor.audit_create(note)
        else:
            auditor.audit_update(note)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Appointment note saved",
        )
        return redirect("mammograms:appointment_note", pk=self.appointment.pk)


class DeleteAppointmentNoteView(DeleteWithAuditView):
    def get_thing_name(self, object):
        return "appointment note"

    def get_success_message_content(self, object):
        return "Appointment note deleted"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.note

    def get_success_url(self):
        return reverse("mammograms:appointment_note", kwargs={"pk": self.kwargs["pk"]})

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except AppointmentNote.DoesNotExist:
            return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AppointmentNote.DoesNotExist:
            return redirect(self.get_success_url())
