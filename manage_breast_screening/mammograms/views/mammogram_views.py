from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from manage_breast_screening.core.utils.date_formatting import format_relative_date
from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
)
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.models.appointment import (
    Appointment,
    AppointmentStatus,
)
from manage_breast_screening.participants.views import parse_return_url


def appointment_should_not_proceed(
    request, appointment_pk, participant_reported_mammogram_pk
):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        ).get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    participant = appointment.screening_episode.participant

    try:
        mammogram = participant.reported_mammograms.get(
            pk=participant_reported_mammogram_pk
        )
    except ParticipantReportedMammogram.DoesNotExist:
        raise Http404("Participant reported mammogram not found")
    exact_date = mammogram.exact_date

    return_url = parse_return_url(request, default="")
    change_previous_mammogram_url = (
        reverse(
            "mammograms:change_previous_mammogram",
            kwargs={
                "pk": appointment_pk,
                "participant_reported_mammogram_pk": participant_reported_mammogram_pk,
            },
        )
        + f"?return_url={return_url}"
    )

    return render(
        request,
        "mammograms/appointment_should_not_proceed.jinja",
        {
            "caption": participant.full_name,
            "page_title": "This appointment should not proceed",
            "heading": "This appointment should not proceed",
            "back_link_params": {
                "href": change_previous_mammogram_url,
                "text": "Go back",
            },
            "appointment": AppointmentPresenter(appointment),
            "time_since_previous_mammogram": format_relative_date(exact_date),
            "change_previous_mammogram_url": change_previous_mammogram_url,
            "return_url": return_url,
        },
    )


@require_http_methods(["POST"])
def attended_not_screened(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")
    appointment.statuses.create(name=AppointmentStatus.ATTENDED_NOT_SCREENED)

    return redirect("clinics:show", pk=appointment.clinic_slot.clinic.pk)
