from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse


def sign_in(request):
    """Single entry point for authentication.

    - In DEBUG: show a developer sign-in button.
    - Otherwise: show a CIS2 sign-in button.
    """
    return render(
        request,
        "auth/sign_in.jinja",
        {
            "page_title": "Sign in",
            "navActive": "sign_in",
            "debug": settings.DEBUG,
        },
    )


def dev_sign_in(request):
    """DEBUG-only: sign in as the first user in the database and redirect to home."""
    if not settings.DEBUG:
        return redirect(reverse("auth:sign_in"))

    User = get_user_model()
    user = User.objects.order_by("pk").first()
    if not user:
        return render(
            request,
            "404.jinja",
            {"error": "No users in the database - can't sign in"},
            status=404,
        )

    auth_login(request, user)
    return redirect(reverse("home"))


def sign_out(request):
    auth_logout(request)
    return redirect(reverse("home"))
