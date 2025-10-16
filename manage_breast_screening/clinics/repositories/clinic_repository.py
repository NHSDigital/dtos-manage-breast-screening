from manage_breast_screening.clinics.models import Clinic
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

    def by_filter(self, filter):
        self._queryset = self._queryset.by_filter(filter)
        return self

    def with_settings(self):
        self._queryset = self._queryset.prefetch_related("setting")
        return self

    def filter_counts(self):
        """
        Get counts of clinics by each filter type. Terminal method.

        Returns:
            dict: Mapping of filter names to counts
        """
        return Clinic.filter_counts(self.provider.pk)
