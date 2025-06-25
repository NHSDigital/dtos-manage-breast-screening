from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from ..participants.models import Appointment, AppointmentStatus
from .models import Clinic
from .presenters import AppointmentListPresenter, ClinicPresenter, ClinicsPresenter


def clinic_list(request, filter="today"):
    clinics = Clinic.objects.prefetch_related("setting").by_filter(filter)
    counts_by_filter = Clinic.filter_counts()
    presenter = ClinicsPresenter(clinics, filter, counts_by_filter)
    return render(
        request,
        "clinics/index.jinja",
        context={"presenter": presenter},
    )


def clinic(request, id, filter="remaining"):
    clinic = Clinic.objects.select_related("setting").get(id=id)
    presented_clinic = ClinicPresenter(clinic)
    appointments = (
        Appointment.objects.for_clinic_and_filter(clinic, filter)
        .prefetch_related("statuses")
        .select_related("clinic_slot__clinic", "screening_episode__participant")
        .order_by("clinic_slot__starts_at")
    )
    counts_by_filter = Appointment.objects.filter_counts_for_clinic(clinic)
    presented_appointment_list = AppointmentListPresenter(
        id, appointments, filter, counts_by_filter
    )
    return render(
        request,
        "clinics/show.jinja",
        context={
            "presented_clinic": presented_clinic,
            "presented_appointment_list": presented_appointment_list,
        },
    )


@require_http_methods(["POST"])
def check_in(_request, id, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

    return redirect("clinics:show", id=id)
