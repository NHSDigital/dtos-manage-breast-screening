from manage_breast_screening.core.repositories.provider_scoped_repository import (
    ProviderScopedRepository,
)
from manage_breast_screening.participants.models import Participant


class ParticipantRepository(ProviderScopedRepository):
    """
    Repository for accessing Participant records scoped to a specific provider.

    A participant is accessible if they have at least one appointment
    with the current provider.
    """

    model_class = Participant

    def _scoped_queryset(self):
        return Participant.objects.filter(
            screeningepisode__appointment__clinic_slot__clinic__setting__provider=self.provider
        ).distinct()
