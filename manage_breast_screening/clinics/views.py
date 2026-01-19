from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)

from ..core.decorators import current_provider_exempt
from ..core.utils.urls import extract_next_path_from_params
from ..participants.models import Appointment
from .models import Clinic, Provider
from .presenters import AppointmentListPresenter, ClinicPresenter, ClinicsPresenter


def clinic_list(request, filter="today"):
    provider = request.user.current_provider
    clinics = provider.clinics.by_filter(filter).prefetch_related("setting")
    counts_by_filter = Clinic.filter_counts(provider.pk)
    presenter = ClinicsPresenter(clinics, filter, counts_by_filter)
    return render(
        request,
        "clinics/index.jinja",
        context={
            "presenter": presenter,
            "page_title": presenter.heading,
            "provider_name": provider.name,
        },
    )


def clinic(request, pk, filter="remaining"):
    provider = request.user.current_provider
    clinic = provider.clinics.get(pk=pk)
    presented_clinic = ClinicPresenter(clinic)
    appointments = (
        clinic.appointments.for_filter(filter)
        .prefetch_current_status()
        .select_related("clinic_slot__clinic", "screening_episode__participant")
        .order_by_starts_at()
    )
    counts_by_filter = Appointment.filter_counts_for_clinic(clinic)
    presented_appointment_list = AppointmentListPresenter(
        pk, appointments, filter, counts_by_filter
    )
    return render(
        request,
        "clinics/show.jinja",
        context={
            "presented_clinic": presented_clinic,
            "presented_appointment_list": presented_appointment_list,
            "page_title": presented_clinic.heading,
        },
    )


@require_http_methods(["POST"])
def check_in(request, pk, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).check_in()

    return redirect("clinics:show", pk=pk)


@current_provider_exempt
@login_required
def select_provider(request):
    next_path = extract_next_path_from_params(request)
    user_providers = Provider.objects.filter(
        assignments__user=request.user, assignments__roles__len__gt=0
    )

    if len(user_providers) == 1:
        request.session["current_provider"] = str(user_providers.first().pk)
        if next_path:
            return redirect(next_path)
        return redirect("clinics:index")

    if request.method == "POST":
        provider_id = request.POST.get("provider")
        if provider_id and user_providers.filter(pk=provider_id).exists():
            request.session["current_provider"] = provider_id
            if next_path:
                return redirect(next_path)
            return redirect("clinics:index")

    return render(
        request,
        "clinics/select_provider.jinja",
        context={
            "providers": user_providers,
            "page_title": "Select Provider",
            "next": next_path,
        },
    )
