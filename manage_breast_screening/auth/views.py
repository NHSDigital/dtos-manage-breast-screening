from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse


@login_not_required
def sign_in(request):
    """Entry point for authentication with CIS2"""
    return render(
        request,
        "auth/sign_in.jinja",
        {
            "page_title": "Sign in",
            "navActive": "sign_in",
        },
    )


def sign_out(request):
    auth_logout(request)
    return redirect(reverse("home"))
