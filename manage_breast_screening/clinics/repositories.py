from manage_breast_screening.core.repositories.base import BaseRepository

from .models import Clinic


class ClinicRepository(BaseRepository):
    """
    Repository for accessing Clinic records scoped to a specific provider.
    """

    model_class = Clinic

    def get_queryset(self):
        """Return clinics scoped to the current provider."""
        return Clinic.objects.filter(setting__provider=self.provider)

    def by_filter(self, filter):
        """
        Get clinics filtered by status (today, upcoming, completed, all).

        Args:
            filter: One of the ClinicFilter enum values

        Returns:
            QuerySet: Filtered and provider-scoped clinics
        """
        return self.get_queryset().by_filter(filter, self.provider.pk)

    def filter_counts(self):
        """
        Get counts of clinics by each filter type.

        Returns:
            dict: Mapping of filter names to counts
        """
        return Clinic.filter_counts(self.provider.pk)
