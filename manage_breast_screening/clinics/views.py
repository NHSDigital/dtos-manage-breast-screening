from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from ..core.decorators import current_provider_exempt
from ..core.utils.urls import extract_next_path_from_params
from ..participants.models import Appointment, AppointmentStatus
from .models import Clinic, Provider
from .presenters import AppointmentListPresenter, ClinicPresenter, ClinicsPresenter


def clinic_list(request, filter="today"):
    current_provider = request.current_provider
    clinics_qs = Clinic.objects.for_provider(current_provider).prefetch_related(
        "setting"
    )
    clinics = clinics_qs.by_filter(filter)
    counts_by_filter = Clinic.filter_counts(provider_id=current_provider)
    presenter = ClinicsPresenter(clinics, filter, counts_by_filter)
    return render(
        request,
        "clinics/index.jinja",
        context={"presenter": presenter, "page_title": presenter.heading},
    )


def clinic(request, pk, filter="remaining"):
    clinic = (
        Clinic.objects.for_provider(request.current_provider)
        .select_related("setting")
        .get(pk=pk)
    )
    presented_clinic = ClinicPresenter(clinic)
    appointments_qs = Appointment.objects.for_provider(request.current_provider)
    appointments = (
        appointments_qs.for_clinic_and_filter(clinic, filter)
        .prefetch_related("statuses")
        .select_related("clinic_slot__clinic", "screening_episode__participant")
        .order_by("clinic_slot__starts_at")
    )
    counts_by_filter = appointments_qs.filter_counts_for_clinic(clinic)
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
def check_in(_request, pk, appointment_pk):
    appointment = get_object_or_404(Appointment, pk=appointment_pk)
    appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

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
