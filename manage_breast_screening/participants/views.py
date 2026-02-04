from logging import getLogger

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from manage_breast_screening.core.utils.safe_redirects import get_safe_redirect_path

from ..participants.models import Appointment
from .forms import EthnicityForm
from .models import Participant

logger = getLogger(__name__)


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

    return_url = get_safe_redirect_path(
        request, reverse("participants:show", kwargs={"pk": participant.pk})
    )

    if request.method == "POST":
        form = EthnicityForm(request.POST, participant=participant)
        if form.is_valid():
            form.save()
            return redirect(return_url)
    else:
        form = EthnicityForm(participant=participant)

    return render(
        request,
        "edit_ethnicity.jinja",
        context={
            "participant": participant,
            "form": form,
            "heading": "Ethnicity",
            "back_link_params": {
                "href": return_url,
            },
            "page_title": "Ethnicity",
        },
    )
