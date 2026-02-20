import logging

from django.db.models import Subquery

from manage_breast_screening.participants.models.participant import Participant

from ..clinics.models import Provider
from .models import Appointment

logger = logging.getLogger(__name__)


def fetch_most_recent_provider(participant_id) -> Provider:
    """
    Fetch the participants current provider; that is, the provider used
    for their most recent appointment.
    """
    most_recent_provider_id = Subquery(
        Appointment.objects.select_related("clinic_slot__clinic__setting__provider")
        .filter(
            screening_episode__participant_id=participant_id,
        )
        .order_by("-clinic_slot__starts_at")
        .values("clinic_slot__clinic__setting__provider_id")[:1]
    )

    return Provider.objects.get(pk=most_recent_provider_id)


def convert_bss_batch_to_participants(bss_batch) -> list[Participant]:
    """
    Convert a BSS batch to a list of Participant objects.
    """
    participants = []
    for record in bss_batch["records"]:
        participants.append(
            Participant(
                nhs_number=record["nhsNumber"],
                first_name=record["givenNames"],
                last_name=record["familyName"],
                date_of_birth=record["birthDate"],
            ).save()
        )

    return participants
