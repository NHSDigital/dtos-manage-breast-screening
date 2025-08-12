from django.urls import path

from . import views

app_name = "demo"

urlpatterns = [
    path("persona-login/", views.persona_login, name="persona_login"),
]
