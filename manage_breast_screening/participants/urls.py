from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = "participants"

urlpatterns = [
    path(
        "<uuid:pk>/",
        views.show,
        name="show",
    ),
    path("", RedirectView.as_view(pattern_name="home"), name="index"),
    path("<uuid:pk>/edit-ethnicity", views.edit_ethnicity, name="edit_ethnicity"),
]
