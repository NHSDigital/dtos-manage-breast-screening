import logging
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.decorators import is_current_provider_exempt

logger = logging.getLogger(__name__)


class CurrentProviderMiddleware:
    """Redirects users to provider selection when `current_provider` is missing.

    Views can be exempted by decorating them with @current_provider_exempt.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
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
