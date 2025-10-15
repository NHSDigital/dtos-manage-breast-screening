from logging import getLogger
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter
from manage_breast_screening.participants.services import fetch_most_recent_provider

from .forms import EthnicityForm, ParticipantReportedMammogramForm
from .models import ParticipantReportedMammogram
from .presenters import ParticipantAppointmentsPresenter, ParticipantPresenter
from .repositories import AppointmentRepository, ParticipantRepository

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
    participant_repo = ParticipantRepository(request.current_provider)
    participant = get_object_or_404(participant_repo.all(), pk=pk)
    presented_participant = ParticipantPresenter(participant)

    appointment_repo = AppointmentRepository(request.current_provider)
    appointments = (
        appointment_repo.for_participant(participant)
        .with_setting()
        .ordered_by_clinic_slot_starts_at(descending=True)
        .all()
    )

    presented_appointments = ParticipantAppointmentsPresenter(
        past_appointments=list(appointments.past()),
        upcoming_appointments=list(appointments.upcoming()),
    )

    last_known_mammograms = ParticipantReportedMammogram.objects.filter(
        participant_id=pk
    ).order_by("-created_at")

    presented_mammograms = LastKnownMammogramPresenter(
        last_known_mammograms,
        participant_pk=pk,
        current_url=request.path,
    )

    return render(
        request,
        "participants/show.jinja",
        context={
            "presented_participant": presented_participant,
            "presented_appointments": presented_appointments,
            "presented_mammograms": presented_mammograms,
            "heading": participant.full_name,
            "page_title": "Participant",
        },
    )


def edit_ethnicity(request, pk):
    participant_repo = ParticipantRepository(request.current_provider)
    participant = get_object_or_404(participant_repo.all(), pk=pk)

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
    participant_repo = ParticipantRepository(request.current_provider)
    participant = get_object_or_404(participant_repo.all(), pk=pk)
    most_recent_provider = fetch_most_recent_provider(pk)
    return_url = parse_return_url(
        request, default=reverse("participants:show", kwargs={"pk": pk})
    )

    if request.method == "POST":
        form = ParticipantReportedMammogramForm(
            data=request.POST,
            participant=participant,
            most_recent_provider=most_recent_provider,
        )
        if form.is_valid():
            form.save()

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
