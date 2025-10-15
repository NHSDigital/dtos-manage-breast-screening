class ProviderScopedRepository:
    """
    Base class for repositories that provide provider-scoped access to models.

    Subclasses must:
    - Set model_class to the Django model they wrap
    - Implement _scoped_queryset() to return a provider-scoped queryset
    """

    model_class = None

    def __init__(self, provider):
        """
        Initialize repository with a provider for scoping queries.

        Args:
            provider: The Provider instance to scope queries to
        """
        if self.model_class is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define model_class"
            )
        self.provider = provider
        self._queryset = self._scoped_queryset()

    def _scoped_queryset(self):
        """
        Return a queryset scoped to the current provider.

        Must be implemented by subclasses to define the scoping logic.

        Returns:
            QuerySet: A filtered queryset containing only records accessible
                     to the current provider
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _scoped_queryset()"
        )

    def all(self):
        """Return all records in the scoped queryset."""
        return self._queryset
