from functools import cached_property

from django.http import Http404
from django.shortcuts import redirect
from rules.contrib.views import PermissionRequiredMixin

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.participants.models import Appointment


class AppointmentMixin:
    """
    A view mixin that exposes the appointment.
    """

    @property
    def appointment_pk(self):
        return self.kwargs["pk"]

    @cached_property
    def appointment(self):
        provider = self.request.user.current_provider
        try:
            return provider.appointments.select_related(
                "clinic_slot__clinic",
                "screening_episode__participant",
                "screening_episode__participant__address",
            ).get(pk=self.appointment_pk)
        except Appointment.DoesNotExist:
            raise Http404


class InProgressAppointmentMixin(PermissionRequiredMixin, AppointmentMixin):
    """
    A view that is only shown with in progress appointments.
    If the appointment is not in progress, redirect to the appointment show page.
    """

    permission_required = Permission.VIEW_MAMMOGRAM_APPOINTMENT

    def dispatch(self, request, *args, **kwargs):
        appointment = self.appointment  # type: ignore
        if not appointment.current_status.in_progress:
            return redirect(
                "mammograms:show_appointment",
                pk=appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)  # type: ignore
