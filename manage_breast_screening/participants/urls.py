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
    path("<uuid:pk>/previous-mammograms/", RedirectView.as_view(pattern_name="show")),
    path("", views.index, name="index"),
    path("<uuid:pk>/edit-ethnicity", views.edit_ethnicity, name="edit_ethnicity"),
    path("upload-bss-batch/", views.upload_bss_batch, name="upload_bss_batch"),
]
