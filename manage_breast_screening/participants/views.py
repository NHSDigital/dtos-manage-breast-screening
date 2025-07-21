from logging import getLogger
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from manage_breast_screening.participants.services import fetch_current_provider

from .forms import EthnicityForm, ParticipantRecordedMammogramForm
from .models import Appointment, Participant
from .presenters import ParticipantAppointmentsPresenter, ParticipantPresenter

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
    participant = get_object_or_404(Participant, pk=pk)
    presented_participant = ParticipantPresenter(participant)

    appointments = (
        Appointment.objects.select_related("clinic_slot__clinic__setting")
        .filter(screening_episode__participant=participant)
        .order_by("-clinic_slot__starts_at")
    )

    presented_appointments = ParticipantAppointmentsPresenter(
        past_appointments=list(appointments.past()),
        upcoming_appointments=list(appointments.upcoming()),
    )

    return render(
        request,
        "participants/show.jinja",
        context={
            "presented_participant": presented_participant,
            "presented_appointments": presented_appointments,
            "heading": participant.full_name,
            "page_title": "Participant",
            "back_link": {
                "text": "Back to participants",
                "href": reverse("participants:index"),
            },
        },
    )


def edit_ethnicity(request, pk):
    participant = get_object_or_404(Participant, pk=pk)

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
            "back_link": {
                "text": "Go back",
                "href": return_url,
            },
            "page_title": "Ethnicity",
        },
    )


def add_previous_mammogram(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    current_provider = fetch_current_provider(pk)
    return_url = parse_return_url(
        request, default=reverse("participants:show", kwargs={"pk": pk})
    )

    if request.method == "POST":
        form = ParticipantRecordedMammogramForm(
            data=request.POST,
            participant=participant,
            current_provider=current_provider,
        )
        if form.is_valid():
            form.save()

            return redirect(return_url)
    else:
        form = ParticipantRecordedMammogramForm(
            participant=participant, current_provider=current_provider
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
