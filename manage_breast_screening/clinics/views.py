from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from ..core.decorators import current_provider_exempt
from ..core.utils.urls import extract_next_path_from_params
from ..participants.models import AppointmentStatus
from ..participants.repositories import AppointmentRepository
from .models import Provider
from .presenters import AppointmentListPresenter, ClinicPresenter, ClinicsPresenter
from .repositories import ClinicRepository


def clinic_list(request, filter="today"):
    clinic_repo = ClinicRepository(request.current_provider)
    clinics = clinic_repo.by_filter(filter).with_settings().all()
    counts_by_filter = clinic_repo.filter_counts()
    presenter = ClinicsPresenter(clinics, filter, counts_by_filter)
    return render(
        request,
        "clinics/index.jinja",
        context={"presenter": presenter, "page_title": presenter.heading},
    )


def clinic(request, pk, filter="remaining"):
    clinic_repo = ClinicRepository(request.current_provider)
    clinic = get_object_or_404(clinic_repo.with_settings().all(), pk=pk)
    presented_clinic = ClinicPresenter(clinic)

    appointment_repo = AppointmentRepository(request.current_provider)
    appointments = (
        appointment_repo.for_clinic_and_filter(clinic, filter)
        .ordered_by_clinic_slot_starts_at()
        .all()
    )
    counts_by_filter = appointment_repo.filter_counts_for_clinic(clinic)
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
    appointment_repo = AppointmentRepository(request.current_provider)
    appointment = get_object_or_404(appointment_repo.all(), pk=appointment_pk)
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
