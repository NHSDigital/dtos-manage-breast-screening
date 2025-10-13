"""
Base repository class for provider-scoped data access.

All repositories should inherit from BaseRepository and implement get_queryset()
to define how their model is scoped to a specific provider.
"""


class BaseRepository:
    """
    Base class for repositories that provide provider-scoped access to models.

    Subclasses must:
    - Set model_class to the Django model they wrap
    - Implement get_queryset() to return a provider-scoped queryset
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

    def get_queryset(self):
        """
        Return a queryset scoped to the current provider.

        Must be implemented by subclasses to define the scoping logic.

        Returns:
            QuerySet: A filtered queryset containing only records accessible
                     to the current provider
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_queryset()"
        )

    def all(self):
        """Return all records scoped to the current provider."""
        return self.get_queryset()

    def filter(self, **kwargs):
        """Filter records scoped to the current provider."""
        return self.get_queryset().filter(**kwargs)

    def get(self, **kwargs):
        """
        Get a single record scoped to the current provider.

        Raises Model.DoesNotExist if not found.
        For views, use get_object_or_404(repo.get_queryset(), pk=pk) instead.
        """
        return self.get_queryset().get(**kwargs)

    def count(self):
        """Count records scoped to the current provider."""
        return self.get_queryset().count()
