from django.conf import settings
from django.urls import path

from . import demo_views, views

app_name = "auth"

urlpatterns = [
    path("sign-in/", views.sign_in, name="sign_in"),
    path("sign-out/", views.sign_out, name="sign_out"),
]

if settings.PERSONAS_ENABLED:
    urlpatterns.append(
        path("persona-login/", demo_views.persona_login, name="persona_login"),
    )
