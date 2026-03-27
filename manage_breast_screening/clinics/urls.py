from django.urls import path

from . import participant_csv_upload_view, views

app_name = "clinics"

urlpatterns = [
    # Clinics
    path("", views.list_clinics, name="list_clinics"),
    path(
        "today/",
        views.list_clinics,
        name="list_clinics_today",
        kwargs={"filter": "today"},
    ),
    path(
        "upcoming/",
        views.list_clinics,
        name="list_clinics_upcoming",
        kwargs={"filter": "upcoming"},
    ),
    path(
        "completed/",
        views.list_clinics,
        name="list_clinics_completed",
        kwargs={"filter": "completed"},
    ),
    path("all/", views.list_clinics, name="index_all", kwargs={"filter": "all"}),
    # Clinic appointments
    path("<uuid:pk>/", views.list_clinic_appointments, name="show_clinic"),
    path(
        "<uuid:pk>/appointments/",
        views.list_clinic_appointments,
        name="list_clinic_appointments_all",
        kwargs={"filter": "all"},
    ),
    path(
        "<uuid:pk>/appointments/remaining/",
        views.list_clinic_appointments,
        name="list_clinic_appointments_remaining",
        kwargs={"filter": "remaining"},
    ),
    path(
        "<uuid:pk>/appointments/checked_in/",
        views.list_clinic_appointments,
        name="list_clinic_appointments_checked_in",
        kwargs={"filter": "checked_in"},
    ),
    path(
        "<uuid:pk>/appointments/in_progress/",
        views.list_clinic_appointments,
        name="list_clinic_appointments_in_progress",
        kwargs={"filter": "in_progress"},
    ),
    path(
        "<uuid:pk>/appointments/complete/",
        views.list_clinic_appointments,
        name="list_clinic_appointments_complete",
        kwargs={"filter": "complete"},
    ),
    path(
        "<uuid:pk>/upload-csv/",
        participant_csv_upload_view.ParticipantCsvUploadView.as_view(),
        name="participant_csv_upload",
    ),
]
