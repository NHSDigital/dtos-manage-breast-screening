from manage_breast_screening.core.repositories.provider_scoped_repository import (
    ProviderScopedRepository,
)
from manage_breast_screening.participants.models import Appointment


class AppointmentRepository(ProviderScopedRepository):
    """
    Repository for accessing Appointment records scoped to a specific provider.
    """

    model_class = Appointment

    def _scoped_queryset(self):
        return Appointment.objects.filter(
            clinic_slot__clinic__setting__provider=self.provider
        )

    def list(self, clinic, filter="all"):
        return (
            self._queryset.for_clinic_and_filter(clinic, filter)
            .ordered_by_clinic_slot_starts_at()
            .prefetch_related("statuses")
            .select_related("clinic_slot__clinic", "screening_episode__participant")
        )

    def list_for_participant(self, participant):
        return (
            self._queryset.filter(screening_episode__participant=participant)
            .select_related("clinic_slot__clinic__setting")
            .ordered_by_clinic_slot_starts_at(descending=True)
        )

    def show(self, pk):
        return self._queryset.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        ).get(pk=pk)

    def filter_counts_for_clinic(self, clinic):
        """
        Get counts of appointments by each filter type for a clinic.
        """
        counts = {}
        for filter in ["remaining", "checked_in", "complete", "all"]:
            counts[filter] = self._queryset.for_clinic_and_filter(
                clinic, filter
            ).count()
        return counts
