from manage_breast_screening.core.repositories.base import BaseRepository

from .models import Appointment, Participant


class AppointmentRepository(BaseRepository):
    """
    Repository for accessing Appointment records scoped to a specific provider.
    """

    model_class = Appointment

    def get_queryset(self):
        """Return appointments scoped to the current provider."""
        return Appointment.objects.filter(
            clinic_slot__clinic__setting__provider=self.provider
        )

    def for_clinic_and_filter(self, clinic, filter):
        """
        Get appointments for a specific clinic filtered by status.

        Args:
            clinic: Clinic instance
            filter: Filter string (remaining, checked_in, complete, all)

        Returns:
            QuerySet: Filtered appointments
        """
        return self.get_queryset().for_clinic_and_filter(clinic, filter)

    def filter_counts_for_clinic(self, clinic):
        """
        Get counts of appointments by each filter type for a clinic.

        Args:
            clinic: Clinic instance

        Returns:
            dict: Mapping of filter names to counts
        """
        return self.get_queryset().filter_counts_for_clinic(clinic)

    def with_full_details(self):
        """
        Return queryset with all related data prefetched for display.

        Useful for appointment detail views that need participant and clinic info.
        """
        return self.get_queryset().select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        )

    def with_list_details(self):
        """
        Return queryset with related data for list views.

        Optimized for displaying lists of appointments with basic info.
        """
        return (
            self.get_queryset()
            .prefetch_related("statuses")
            .select_related("clinic_slot__clinic", "screening_episode__participant")
        )


class ParticipantRepository(BaseRepository):
    """
    Repository for accessing Participant records scoped to a specific provider.

    A participant is accessible if they have at least one appointment
    with the current provider.
    """

    model_class = Participant

    def get_queryset(self):
        """Return participants who have appointments with the current provider."""
        return Participant.objects.filter(
            screeningepisode__appointment__clinic_slot__clinic__setting__provider=self.provider
        ).distinct()
