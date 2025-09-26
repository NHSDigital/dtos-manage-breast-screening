from django.db.models import Subquery

from ..clinics.models import Provider
from .models import Appointment


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
