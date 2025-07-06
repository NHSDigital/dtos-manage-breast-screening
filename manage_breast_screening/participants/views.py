from logging import getLogger

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EthnicityForm
from .models import Appointment, Participant
from .presenters import ParticipantAppointmentsPresenter, ParticipantPresenter

logger = getLogger(__name__)


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
        },
    )
