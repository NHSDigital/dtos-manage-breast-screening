from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)
from manage_breast_screening.core.views.generic import DeleteWithAuditView
from manage_breast_screening.participants.models import AppointmentNote


class AppointmentNoteMixin:
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
        return_url = self.get_success_url()
        return redirect(return_url)


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
        return extract_relative_redirect_url(
            self.request,
            default=reverse(
                "mammograms:appointment_note", kwargs={"pk": self.kwargs["pk"]}
            ),
        )

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
