from manage_breast_screening.clinics.models import Clinic, ClinicFilter
from manage_breast_screening.core.repositories.provider_scoped_repository import (
    ProviderScopedRepository,
)


class ClinicRepository(ProviderScopedRepository):
    """
    Repository for accessing Clinic records scoped to a specific provider.
    """

    model_class = Clinic

    def _scoped_queryset(self):
        return Clinic.objects.filter(setting__provider=self.provider)

    def list(self, filter="all"):
        return self._queryset.by_filter(filter).prefetch_related("setting")

    def get(self, pk):
        return self._queryset.get(pk=pk)

    def filter_counts(self):
        """
        Get counts of clinics by each filter type. Terminal method.

        Returns:
            dict: Mapping of filter names to counts
        """
        return {
            ClinicFilter.ALL: self._queryset.count(),
            ClinicFilter.TODAY: self._queryset.today().count(),
            ClinicFilter.UPCOMING: self._queryset.upcoming().count(),
            ClinicFilter.COMPLETED: self._queryset.completed().count(),
        }
