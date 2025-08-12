"""
URL configuration for manage_breast_screening project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import URLPattern, URLResolver, include, path, reverse_lazy
from django.views.generic.base import RedirectView


def require_auth(view):
    """Wrap a view with login_required using our sign-in route."""
    wrapped = login_required(view, login_url=reverse_lazy("auth:sign_in"))
    setattr(wrapped, "_mbs_protected", True)
    return wrapped


def protect_urlpatterns(urlpatterns, skip_namespaces: set | None = None):
    """Recursively wrap URLPattern callbacks with login_required.

    Namespaces in skip_namespaces are excluded (e.g., 'auth', 'admin', 'djdt').
    """
    if skip_namespaces is None:
        skip_namespaces = {"auth", "admin", "djdt"}

    for p in urlpatterns:
        if isinstance(p, URLResolver):
            # Skip whole namespaces (e.g., auth, admin, djdt)
            if (
                getattr(p, "namespace", None) in skip_namespaces
                or getattr(p, "app_name", None) in skip_namespaces
            ):
                continue
            protect_urlpatterns(p.url_patterns, skip_namespaces)
        elif isinstance(p, URLPattern):
            # Don't double-wrap
            if not getattr(p.callback, "_mbs_protected", False):
                p.callback = require_auth(p.callback)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "auth/",
        include(("manage_breast_screening.auth.urls", "auth"), namespace="auth"),
    ),
    path(
        "clinics/", include("manage_breast_screening.clinics.urls", namespace="clinics")
    ),
    path(
        "mammograms/",
        include(
            "manage_breast_screening.mammograms.urls",
            namespace="mammograms",
        ),
    ),
    path(
        "participants/",
        include("manage_breast_screening.participants.urls", namespace="participants"),
    ),
    path("", RedirectView.as_view(pattern_name="clinics:index"), name="home"),
]

if settings.DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()

# TODO: remove the DEV_SIGN_IN check once we've implemented CIS2 auth. For now,
# we only apply auth protection when a viable auth method is available. This keeps our
# tests passing and prevents us forcing a sign in without a way to do so.
if settings.DEV_SIGN_IN:
    # Apply auth protection to all routes except whitelisted namespaces
    protect_urlpatterns(urlpatterns)
