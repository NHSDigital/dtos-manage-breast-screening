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
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic.base import RedirectView


@login_not_required
def sha_view(reviews):
  return HttpResponse(settings.COMMIT_SHA)

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
        "notifications/",
        include(
            "manage_breast_screening.notifications.urls",
            namespace="notifications",
        ),
    ),
    path(
        "participants/",
        include("manage_breast_screening.participants.urls", namespace="participants"),
    ),
    path(
        "sha/",
        sha_view,
    ),
    path("", RedirectView.as_view(pattern_name="clinics:index"), name="home"),
]

if settings.DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()
