from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = "participants"

urlpatterns = [
    path(
        "<uuid:pk>/",
        views.show_view,
        name="show_participant",
    ),
    path(
        "<uuid:pk>/previous-mammograms/",
        RedirectView.as_view(pattern_name="show_participant"),
    ),
    path("", RedirectView.as_view(pattern_name="home"), name="index"),
    path(
        "<uuid:pk>/edit-ethnicity/",
        views.update_ethnicity_view,
        name="update_ethnicity",
    ),
]
