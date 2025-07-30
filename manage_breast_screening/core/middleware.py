from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseForbidden

from manage_breast_screening.core.utils.auth import parse_basic_auth


class BasicAuthMiddleware:
    """
    Perform HTTP basic authentication on any requests where the user is not already
    logged in.

    This middleware is enabled in public-facing, non-production environments where
    data confidentiality is not needed, but we don't want people confusing
    the app with a real service. It's not intended as a secure authentication
    mechanism.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        if not settings.BASIC_AUTH_ENABLED:
            return HttpResponseForbidden()

        if "HTTP_AUTHORIZATION" not in request.META:
            # Send the basic authentication challenge
            return HttpResponse(
                status=401,
                headers={
                    "WWW-Authenticate": f"Basic realm='{settings.BASIC_AUTH_REALM}'"
                },
            )

        # Parse the authorization header
        auth = request.META["HTTP_AUTHORIZATION"]
        try:
            username, password = parse_basic_auth(auth)
        except ValueError:
            return HttpResponseForbidden()

        # Authenticate the provided username and password
        user = authenticate(username=username, password=password)

        # Log in the corresponding user
        if user:
            login(request, user)
            return self.get_response(request)

        return HttpResponseForbidden()
