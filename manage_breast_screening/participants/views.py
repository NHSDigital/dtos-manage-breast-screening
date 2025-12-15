from datetime import date
from logging import getLogger
from urllib.parse import urlparse

from dateutil.relativedelta import relativedelta
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
)
from manage_breast_screening.participants.services import fetch_most_recent_provider

from ..participants.models import Appointment, AppointmentStatus
from .forms import EthnicityForm, ParticipantReportedMammogramForm
from .models import Participant

logger = getLogger(__name__)


def parse_return_url(request, default: str) -> str:
    """
    Parse the return_url from the request, with a fallback,
    and validating that the URL is not external to the service.
    """
    return_url = (
        request.POST.get("return_url")
        if request.method == "POST"
        else request.GET.get("return_url")
    )

    if not return_url or urlparse(return_url).netloc:
        return default

    return return_url


def show(request, pk):
    provider = request.user.current_provider
    try:
        appointment_id = (
            provider.appointments.select_related("clinic_slot")
            .for_participant(pk)
            .order_by_starts_at(desc=True)[0:1]
            .values_list("id", flat=True)
            .get()
        )
    except Appointment.DoesNotExist:
        logger.exception(f"Appointment not found for participant {pk}")
        return redirect(reverse("clinics:index"))

    return redirect("mammograms:participant_details", pk=appointment_id)


def edit_ethnicity(request, pk):
    try:
        provider = request.user.current_provider
        participant = provider.participants.get(pk=pk)
    except Participant.DoesNotExist:
        raise Http404("Participant not found")

    if request.method == "POST":
        return_url = request.POST.get("return_url")
        form = EthnicityForm(request.POST, participant=participant)
        if form.is_valid():
            form.save()
            return redirect(return_url)
    else:
        return_url = request.GET.get("return_url")
        form = EthnicityForm(participant=participant)

    return_url = return_url or reverse(
        "participants:show", kwargs={"pk": participant.pk}
    )

    return render(
        request,
        "edit_ethnicity.jinja",
        context={
            "participant": participant,
            "form": form,
            "heading": "Ethnicity",
            "back_link_params": {
                "text": "Go back",
                "href": return_url,
            },
            "page_title": "Ethnicity",
        },
    )


def add_previous_mammogram(request, appointment_pk):
    provider = request.user.current_provider
    appointment = provider.appointments.select_related(
        "clinic_slot__clinic",
        "screening_episode__participant",
        "screening_episode__participant__address",
    ).get(pk=appointment_pk)
    participant_pk = appointment.screening_episode.participant.pk
    try:
        participant = provider.participants.get(pk=participant_pk)
    except Participant.DoesNotExist:
        raise Http404("Participant not found")
    most_recent_provider = fetch_most_recent_provider(participant_pk)
    return_url = parse_return_url(
        request, default=reverse("participants:show", kwargs={"pk": participant_pk})
    )

    if request.method == "POST":
        form = ParticipantReportedMammogramForm(
            data=request.POST,
            participant=participant,
            most_recent_provider=most_recent_provider,
        )
        if form.is_valid():
            form.save()

            exact_date = form.cleaned_data.get("exact_date")
            if exact_date and exact_date > date.today() - relativedelta(months=6):
                return redirect(
                    reverse(
                        "participants:appointment_should_not_proceed",
                        kwargs={"appointment_pk": appointment_pk},
                    )
                )

            return redirect(return_url)
    else:
        form = ParticipantReportedMammogramForm(
            participant=participant, most_recent_provider=most_recent_provider
        )

    return render(
        request,
        "participants/add_previous_mammogram.jinja",
        {
            "title": "Add details of a previous mammogram",
            "caption": participant.full_name,
            "page_title": "Add details of a previous mammogram",
            "form": form,
            "back_link_params": {"href": return_url, "text": "Go back"},
            "return_url": return_url,
        },
    )


def appointment_should_not_proceed(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        ).get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")
    participant_pk = appointment.screening_episode.participant.pk
    participant = provider.participants.get(pk=participant_pk)

    return_url = parse_return_url(
        request, default=reverse("participants:show", kwargs={"pk": participant_pk})
    )

    return render(
        request,
        "participants/appointment_should_not_proceed.jinja",
        {
            "caption": participant.full_name,
            "page_title": "This appointment should not proceed",
            "heading": "This appointment should not proceed",
            "back_link_params": {"href": return_url, "text": "Go back"},
            "appointment": AppointmentPresenter(appointment),
        },
    )


@require_http_methods(["POST"])
def attended_not_screened(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")
    appointment.statuses.create(state=AppointmentStatus.DID_NOT_ATTEND)

    return redirect("clinics:show", pk=appointment.clinic_slot.clinic.pk)
