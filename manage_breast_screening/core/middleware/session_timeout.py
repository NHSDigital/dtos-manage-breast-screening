import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


class SessionTimeoutMiddleware:
    """
    Enforces both inactivity timeout and hard timeout for user sessions.

    Inactivity timeout: Sessions expire after SESSION_INACTIVITY_TIMEOUT seconds
    of no requests (default: 15 minutes). Optimized to reduce database writes by
    only updating last_activity if more than SESSION_ACTIVITY_UPDATE_THRESHOLD
    seconds have passed (default: 60s).

    Hard timeout: Sessions expire after SESSION_HARD_TIMEOUT seconds regardless
    of activity (default: 12 hours).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.inactivity_timeout = getattr(settings, "SESSION_INACTIVITY_TIMEOUT", 900)
        self.hard_timeout = getattr(settings, "SESSION_HARD_TIMEOUT", 43200)
        self.update_threshold = getattr(
            settings, "SESSION_ACTIVITY_UPDATE_THRESHOLD", 60
        )

    def _logout_and_redirect(self, request):
        auth_logout(request)
        return redirect(reverse("auth:login"))

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        now = timezone.now()

        login_time_str = request.session.get("login_time")
        if not login_time_str:
            logger.warning(
                "Missing login_time for user %s, forcing logout",
                request.user.id,
            )
            return self._logout_and_redirect(request)
        login_time = datetime.fromisoformat(login_time_str)
        elapsed_since_login = (now - login_time).total_seconds()
        if elapsed_since_login > self.hard_timeout:
            logger.info(
                "Hard timeout reached for user %s after %ss",
                request.user.id,
                elapsed_since_login,
            )
            return self._logout_and_redirect(request)

        last_activity_str = request.session.get("last_activity")
        if last_activity_str:
            last_activity = datetime.fromisoformat(last_activity_str)
            inactive_seconds = (now - last_activity).total_seconds()
            if inactive_seconds > self.inactivity_timeout:
                logger.info(
                    "Inactivity timeout for user %s after %ss",
                    request.user.id,
                    inactive_seconds,
                )
                return self._logout_and_redirect(request)

            if inactive_seconds < self.update_threshold:
                return self.get_response(request)

        request.session["last_activity"] = now.isoformat()
        request.session.modified = True
        return self.get_response(request)
