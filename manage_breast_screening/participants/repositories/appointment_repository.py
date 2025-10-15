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

    def ordered_by_clinic_slot_starts_at(self, descending=False):
        order_field = (
            "-clinic_slot__starts_at" if descending else "clinic_slot__starts_at"
        )
        self._queryset = self._queryset.order_by(order_field)
        return self

    def for_participant(self, participant):
        self._queryset = self._queryset.filter(
            screening_episode__participant=participant
        )
        return self

    def for_clinic_and_filter(self, clinic, filter):
        self._queryset = self._queryset.for_clinic_and_filter(clinic, filter)
        return self

    def with_setting(self):
        self._queryset = self._queryset.select_related("clinic_slot__clinic__setting")
        return self

    def with_full_details(self):
        self._queryset = self._queryset.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        )
        return self

    def with_list_details(self):
        self._queryset = self._queryset.prefetch_related("statuses").select_related(
            "clinic_slot__clinic", "screening_episode__participant"
        )
        return self

    def filter_counts_for_clinic(self, clinic):
        """
        Get counts of appointments by each filter type for a clinic. Terminal method.
        """
        return Appointment.objects.filter_counts_for_clinic(clinic)
