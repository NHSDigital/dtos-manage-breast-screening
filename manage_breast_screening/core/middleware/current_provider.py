import logging
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.clinics.models import Provider
from manage_breast_screening.core.decorators import is_current_provider_exempt

logger = logging.getLogger(__name__)


class CurrentProviderMiddleware:
    """Redirects users to provider selection when `current_provider` is missing.

    Views can be exempted by decorating them with @current_provider_exempt.

    Also adds a `current_provider` attribute to the request object that lazily
    loads the Provider instance from the database.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        self._add_current_provider_property(request)
        return self.get_response(request)

    def process_view(
        self, request: HttpRequest, view_func, _view_args, _view_kwargs
    ) -> Optional[HttpResponse]:
        if not request.user.is_authenticated:
            return None

        if request.session.get("current_provider"):
            return None

        # Skip if the view has been marked as exempt
        if is_current_provider_exempt(view_func):
            return None

        return redirect(reverse("clinics:select_provider"))

    def _add_current_provider_property(self, request: HttpRequest) -> None:
        """Add current_provider attribute to request.

        Loads the Provider instance from the database based on the
        current_provider session value.
        """
        provider_id = request.session.get("current_provider")
        if provider_id:
            request.current_provider = Provider.objects.get(pk=provider_id)
        else:
            request.current_provider = None
