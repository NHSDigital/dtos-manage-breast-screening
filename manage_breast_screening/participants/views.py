from logging import getLogger
from urllib.parse import urlparse

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from ..participants.models import Appointment
from .forms import EthnicityForm
from .models import Participant

logger = getLogger(__name__)


def parse_return_url(request, default: str) -> str:
    """
    Parse the return_url from the request, with a fallback,
    and validating that the URL is not external to the service.
    """
    return_url = request.POST.get("return_url") or request.GET.get("return_url")

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
