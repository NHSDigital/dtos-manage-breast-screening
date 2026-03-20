from typing import Callable, Optional

from django.conf import settings
from django.http import HttpResponse

from manage_breast_screening.core.decorators import is_service_enabled_exempt


class ServiceEnabledMiddleware:
    """Returns 503 for all non-exempt views when SERVICE_ENABLED=False.

    Exempt views (healthcheck, sha, robots.txt) continue to respond normally
    so that Azure Container Apps health probes don't interpret the outage as a
    container failure and attempt to restart instances.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(
        self, request, view_func, view_args, view_kwargs
    ) -> Optional[HttpResponse]:
        if getattr(settings, "SERVICE_ENABLED", True):
            return None

        if is_service_enabled_exempt(view_func):
            return None

        return HttpResponse("Service unavailable", status=503)
