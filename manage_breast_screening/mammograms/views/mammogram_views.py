from datetime import date, datetime
from urllib.parse import urlparse

from dateutil.relativedelta import relativedelta
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from manage_breast_screening.core.utils.date_formatting import format_relative_date
from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
)
from manage_breast_screening.participants.forms import ParticipantReportedMammogramForm
from manage_breast_screening.participants.models.appointment import (
    Appointment,
    AppointmentStatus,
)
from manage_breast_screening.participants.models.participant import Participant
from manage_breast_screening.participants.services import fetch_most_recent_provider


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
                        "mammograms:appointment_should_not_proceed",
                        kwargs={"appointment_pk": appointment_pk},
                    )
                    + f"?exact_date={exact_date.isoformat()}"
                )

            return redirect(return_url)
    else:
        form = ParticipantReportedMammogramForm(
            participant=participant, most_recent_provider=most_recent_provider
        )

    return render(
        request,
        "mammograms/add_previous_mammogram.jinja",
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
    exact_date = datetime.strptime(request.GET.get("exact_date"), "%Y-%m-%d").date()

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
        "mammograms/appointment_should_not_proceed.jinja",
        {
            "caption": participant.full_name,
            "page_title": "This appointment should not proceed",
            "heading": "This appointment should not proceed",
            "back_link_params": {"href": return_url, "text": "Go back"},
            "appointment": AppointmentPresenter(appointment),
            "time_since_previous_mammogram": format_relative_date(exact_date),
        },
    )


@require_http_methods(["POST"])
def attended_not_screened(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")
    appointment.statuses.create(state=AppointmentStatus.ATTENDED_NOT_SCREENED)

    return redirect("clinics:show", pk=appointment.clinic_slot.clinic.pk)


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
