from django.conf import settings
from django.contrib.auth.middleware import (
    AuthenticationMiddleware,
    LoginRequiredMiddleware,
)


class ManageAuthenticationMiddleware(AuthenticationMiddleware):
    """
    Custom middleware that extends AuthenticationMiddleware to allow
    unauthenticated access to api paths.
    """

    def process_request(self, request):
        if not request.path.startswith(settings.API_PATH_PREFIX):
            super().process_request(request)


class ManageLoginRequiredMiddleware(LoginRequiredMiddleware):
    """
    Custom middleware that extends LoginRequiredMiddleware to allow
    unauthenticated access to api paths.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith(settings.API_PATH_PREFIX):
            return None

        return super().process_view(request, view_func, view_args, view_kwargs)
