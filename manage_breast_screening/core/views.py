from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect

from manage_breast_screening.core.utils.auth import parse_basic_auth


@login_not_required
def test_environment_login(request):
    """
    A login page that performs basic authentication and redirects back to
    the home page if successful.

    This login page is enabled in public-facing, non-production environments where
    data confidentiality is not needed, but we don't want people confusing
    the app with a real service. It's not intended as a secure authentication
    mechanism.
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect("/")

    if not settings.BASIC_AUTH_ENABLED:
        return HttpResponseForbidden()

    if "HTTP_AUTHORIZATION" not in request.META:
        # Send the basic authentication challenge
        return HttpResponse(
            status=401,
            headers={"WWW-Authenticate": f"Basic realm='{settings.BASIC_AUTH_REALM}'"},
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
        return HttpResponseRedirect("/")

    return HttpResponseForbidden()
