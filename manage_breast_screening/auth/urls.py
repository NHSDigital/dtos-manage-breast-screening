from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    path("sign-in/", views.sign_in, name="sign_in"),
    path("dev-sign-in/", views.dev_sign_in, name="dev_sign_in"),
    path("sign-out/", views.sign_out, name="sign_out"),
]
