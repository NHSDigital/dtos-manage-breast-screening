from django.conf import settings
from django.urls import path

from . import demo_views, views

app_name = "auth"

urlpatterns = [
    path("log-in/", views.login, name="login"),
    path("log-out/", views.logout, name="logout"),
    # CIS2 OpenID Connect
    path("cis2/log-in/", views.cis2_login, name="cis2_login"),
    path("cis2/callback/", views.cis2_callback, name="cis2_callback"),
    path(
        "cis2/back-channel-logout/",
        views.cis2_back_channel_logout,
        name="cis2_back_channel_logout",
    ),
    # JWKS endpoint for private_key_jwt
    path("cis2/jwks_uri", views.jwks, name="jwks"),
]

if settings.PERSONAS_ENABLED:
    urlpatterns.append(
        path("persona-login/", demo_views.persona_login, name="persona_login"),
    )
