from django.urls import path

from . import views

app_name = "clinics"

urlpatterns = [
    # Provider selection
    path("select-provider/", views.select_provider, name="select_provider"),
    # Clinic list
    path("", views.clinic_list, name="index"),
    path("today/", views.clinic_list, name="index_today", kwargs={"filter": "today"}),
    path(
        "upcoming/",
        views.clinic_list,
        name="index_upcoming",
        kwargs={"filter": "upcoming"},
    ),
    path(
        "completed/",
        views.clinic_list,
        name="index_completed",
        kwargs={"filter": "completed"},
    ),
    path("all/", views.clinic_list, name="index_all", kwargs={"filter": "all"}),
    # Clinic show
    path("<uuid:pk>/", views.clinic, name="show"),
    path(
        "<uuid:pk>/remaining/",
        views.clinic,
        name="show_remaining",
        kwargs={"filter": "remaining"},
    ),
    path(
        "<uuid:pk>/checked_in/",
        views.clinic,
        name="show_checked_in",
        kwargs={"filter": "checked_in"},
    ),
    path(
        "<uuid:pk>/complete/",
        views.clinic,
        name="show_complete",
        kwargs={"filter": "complete"},
    ),
    path("<uuid:pk>/all/", views.clinic, name="show_all", kwargs={"filter": "all"}),
    path(
        "<uuid:pk>/appointment/<uuid:appointment_pk>/check-in/",
        views.check_in,
        name="check_in",
    ),
]
