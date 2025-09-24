import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse

logger = logging.getLogger(__name__)


class CurrentProviderMiddleware:
    """Redirects users to provider selection when `current_provider` is missing."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.select_provider_url = reverse("clinics:select_provider")
        self.exempt_view_names = {
            "clinics:select_provider",
            "auth:logout",
            "auth:login",
            "auth:cis2_login",
            "auth:cis2_callback",
            "auth:cis2_back_channel_logout",
            "auth:jwks",
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.session.get("current_provider"):
            return self.get_response(request)

        if request.path == self.select_provider_url:
            return self.get_response(request)

        try:
            view_name = resolve(request.path_info).view_name
        except Resolver404:
            return self.get_response(request)

        if view_name in self.exempt_view_names:
            return self.get_response(request)

        logger.debug("Redirecting to provider selection for missing current_provider")
        return redirect(self.select_provider_url)
