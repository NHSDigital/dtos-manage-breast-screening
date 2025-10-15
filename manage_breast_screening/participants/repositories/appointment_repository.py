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

    def ordered_by_clinic_slot_starts_at(self):
        """
        Order appointments by clinic slot start time.

        Returns:
            self: For method chaining
        """
        self._queryset = self._queryset.order_by("clinic_slot__starts_at")
        return self

    def for_clinic_and_filter(self, clinic, filter):
        """
        Filter appointments for a specific clinic filtered by status.

        Args:
            clinic: Clinic instance
            filter: Filter string (remaining, checked_in, complete, all)

        Returns:
            self: For method chaining
        """
        self._queryset = self._queryset.for_clinic_and_filter(clinic, filter)
        return self

    def with_full_details(self):
        """
        Apply prefetching for all related data needed for display.

        Useful for appointment detail views that need participant and clinic info.

        Returns:
            self: For method chaining
        """
        self._queryset = self._queryset.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        )
        return self

    def with_list_details(self):
        """
        Apply prefetching for related data needed for list views.

        Optimized for displaying lists of appointments with basic info.

        Returns:
            self: For method chaining
        """
        self._queryset = self._queryset.prefetch_related("statuses").select_related(
            "clinic_slot__clinic", "screening_episode__participant"
        )
        return self

    def filter_counts_for_clinic(self, clinic):
        """
        Get counts of appointments by each filter type for a clinic. Terminal method.

        Args:
            clinic: Clinic instance

        Returns:
            dict: Mapping of filter names to counts
        """
        return Appointment.objects.filter_counts_for_clinic(clinic)
