from __future__ import annotations

from typing import Any

from django.db import models


class ProviderScopedQuerySet(models.QuerySet):
    """
    Base queryset for models that must be filtered by provider.

    Subclasses must implement `_provider_filter_kwargs` to describe how the
    current provider should be applied to the queryset.
    """

    def for_provider(self, provider: Any):
        """
        Scope the queryset to records that belong to the given provider.

        Accepts either a Provider instance or a provider primary key.
        """
        provider_id = self._extract_provider_id(provider)
        return self.filter(**self._provider_filter_kwargs(provider_id))

    def _provider_filter_kwargs(self, provider_id: Any) -> dict[str, Any]:
        """
        Return filter kwargs that scope the queryset to the given provider.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _provider_filter_kwargs()"
        )

    @staticmethod
    def _extract_provider_id(provider: Any) -> Any:
        if provider is None:
            raise ValueError("provider must be provided")

        provider_id = getattr(provider, "pk", provider)
        if provider_id is None:
            raise ValueError("provider must have a primary key")

        return provider_id
