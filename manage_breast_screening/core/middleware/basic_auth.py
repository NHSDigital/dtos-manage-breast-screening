import base64
import hmac
import logging
from typing import Callable, Optional

from django.conf import settings
from django.http import HttpResponse

from manage_breast_screening.core.decorators import is_basic_auth_exempt

logger = logging.getLogger(__name__)


class BasicAuthMiddleware:
    """Simple HTTP Basic Auth middleware.

    Enabled when settings.BASIC_AUTH_ENABLED is True. Credentials are checked
    against settings.BASIC_AUTH_USERNAME and settings.BASIC_AUTH_PASSWORD.

    Exemptions:
    - Views decorated with an attribute `basic_auth_exempt = True` (set by our decorator)
    - Debug toolbar URLs when settings.DEBUG_TOOLBAR is True
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(
        self, request, view_func, view_args, view_kwargs
    ) -> Optional[HttpResponse]:
        if not getattr(settings, "BASIC_AUTH_ENABLED"):
            return None

        # Skip debug toolbar explicitly
        if getattr(settings, "DEBUG_TOOLBAR", False) and request.path.startswith(
            "/__debug__/"
        ):
            return None

        # Skip if the view has been marked as exempt
        if is_basic_auth_exempt(view_func):
            return None

        # Validate Authorization header
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Basic "):
            return self._unauthorized_response()
        try:
            b64_part = header.split(" ", 1)[1].strip()
            decoded = base64.b64decode(b64_part).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return self._unauthorized_response()

        expected_username = getattr(settings, "BASIC_AUTH_USERNAME", None)
        expected_password = getattr(settings, "BASIC_AUTH_PASSWORD", None)

        if not expected_username or not expected_password:
            return self._unauthorized_response()

        if hmac.compare_digest(username, expected_username) and hmac.compare_digest(
            password, expected_password
        ):
            return None

        return self._unauthorized_response()

    def _unauthorized_response(self) -> HttpResponse:
        realm = getattr(settings, "BASIC_AUTH_REALM", "Restricted")
        response = HttpResponse("Unauthorized", status=401)
        response["WWW-Authenticate"] = f'Basic realm="{realm}"'
        return response
