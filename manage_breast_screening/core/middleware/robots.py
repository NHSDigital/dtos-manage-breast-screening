from typing import Callable

from django.http import HttpRequest, HttpResponse


class RobotsTagMiddleware:
    """Middleware to add X-Robots-Tag header to all responses.

    This header instructs search engine crawlers not to index pages or follow links.
    Applied to all environments to prevent indexing of the service.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        return response
