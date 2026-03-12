import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rules.contrib.views import permission_required

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.participants.models.appointment import AppointmentStatus
from manage_breast_screening.participants.models.participant import Participant

from ..core.decorators import current_provider_exempt
from ..core.utils.relative_redirects import extract_relative_redirect_url
from ..participants.models import Appointment, ScreeningEpisode
from .forms import UpdateProviderSettingsForm
from .models import Clinic, ClinicSlot, Provider
from .presenters import AppointmentListPresenter, ClinicPresenter, ClinicsPresenter
from .services import get_user_providers_with_roles

logger = logging.getLogger(__name__)


def list_clinics(request, filter="today"):
    provider = request.user.current_provider
    clinics = provider.clinics.by_filter(filter).prefetch_related("setting")
    counts_by_filter = Clinic.filter_counts(provider.pk)
    presenter = ClinicsPresenter(clinics, filter, counts_by_filter)
    return render(
        request,
        "clinics/list_clinics.jinja",
        context={
            "presenter": presenter,
            "page_title": presenter.heading,
            "provider_name": provider.name,
        },
    )


def list_clinic_appointments(request, pk, filter="remaining"):
    provider = request.user.current_provider
    clinic = provider.clinics.get(pk=pk)
    presented_clinic = ClinicPresenter(clinic)
    appointments = (
        clinic.appointments.for_filter(filter)
        .prefetch_current_status()
        .prefetch_related("note")
        .select_related("clinic_slot__clinic", "screening_episode__participant")
        .order_by_starts_at()
    )
    counts_by_filter = Appointment.filter_counts_for_clinic(clinic)
    presented_appointment_list = AppointmentListPresenter(
        pk, appointments, filter, counts_by_filter
    )
    return render(
        request,
        "clinics/list_clinic_appointments.jinja",
        context={
            "presented_clinic": presented_clinic,
            "presented_appointment_list": presented_appointment_list,
            "page_title": presented_clinic.heading,
        },
    )


@require_http_methods(["POST"])
def check_in_appointment(request, pk, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).check_in()

    return redirect("clinics:show_clinic", pk=pk)


@current_provider_exempt
@login_required
def select_provider(request):
    next_path = extract_relative_redirect_url(request, parameter_name="next")

    user_providers = get_user_providers_with_roles(request.user)

    if len(user_providers) == 1:
        request.session["current_provider"] = str(user_providers.first().pk)
        if next_path:
            return redirect(next_path)
        return redirect("clinics:list_clinics")

    if request.method == "POST":
        provider_id = request.POST.get("provider")
        if provider_id and user_providers.filter(pk=provider_id).exists():
            request.session["current_provider"] = provider_id
            if next_path:
                return redirect(next_path)
            return redirect("clinics:list_clinics")

    return render(
        request,
        "clinics/select_provider.jinja",
        context={
            "providers": user_providers,
            "page_title": "Select Provider",
            "next": next_path,
        },
    )


@require_http_methods(["GET", "POST"])
@permission_required(Permission.MANAGE_PROVIDER_SETTINGS, raise_exception=True)
def update_provider_settings(request):
    provider = request.user.current_provider
    config = provider.get_config()

    if request.method == "POST":
        form = UpdateProviderSettingsForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved successfully.")
            return redirect("update_provider_settings")
    else:
        form = UpdateProviderSettingsForm(instance=config)

    return render(
        request,
        "clinics/update_provider_settings.jinja",
        context={
            "form": form,
            "provider": provider,
            "page_title": "Provider settings",
        },
    )


def add_participants(request, pk):
    if request.method == "POST":
        participant = Participant.objects.get(pk=request.POST.get("participant"))
        clinic = Clinic.objects.get(pk=pk)
        clinic_slots = ClinicSlot.objects.filter(clinic=clinic).order_by("starts_at")
        screening_episode = ScreeningEpisode.objects.create(participant=participant)
        appt = Appointment.objects.create(
            screening_episode_id=screening_episode.id, clinic_slot=clinic_slots.last()
        )
        appt.set_status(
            status_name=AppointmentStatus.YET_TO_BEGIN_STATUSES[0],
            created_by=request.user,
        )
        appt.save()

        return redirect("clinics:show_clinic", pk=pk)

    participants = Participant.objects.filter(first_name__icontains="bss").order_by(
        "first_name"
    )
    return render(
        request,
        "clinics/add_participants.jinja",
        context={
            "participants": participants,
            "clinic_pk": pk,
        },
    )
