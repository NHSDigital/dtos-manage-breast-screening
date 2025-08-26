from django.conf import settings
from django.urls import path

from . import demo_views, views

app_name = "auth"

urlpatterns = [
    path("sign-in/", views.sign_in, name="sign_in"),
    path("sign-out/", views.sign_out, name="sign_out"),
    # CIS2 OpenID Connect
    path("cis2/sign-in/", views.cis2_sign_in, name="cis2_sign_in"),
    path("cis2/callback/", views.cis2_callback, name="cis2_callback"),
    # JWKS endpoint for private_key_jwt
    path("cis2/jwks_uri", views.jwks, name="jwks"),
]

if settings.PERSONAS_ENABLED:
    urlpatterns.append(
        path("persona-login/", demo_views.persona_login, name="persona_login"),
    )
