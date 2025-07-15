from django.urls import path

from . import views

app_name = "mammograms"

urlpatterns = [
    path(
        "<uuid:pk>/check-in/",
        views.check_in,
        name="check_in",
    ),
    path(
        "<uuid:pk>/",
        views.StartScreening.as_view(),
        name="show_appointment",
    ),
    path(
        "<uuid:pk>/ask-for-medical-information/",
        views.AskForMedicalInformation.as_view(),
        name="ask_for_medical_information",
    ),
    path(
        "<uuid:pk>/record-medical-information/",
        views.RecordMedicalInformation.as_view(),
        name="record_medical_information",
    ),
    path(
        "<uuid:pk>/awaiting-images/",
        views.awaiting_images,
        name="awaiting_images",
    ),
    path(
        "<uuid:pk>/cannot-go-ahead/",
        views.appointment_cannot_go_ahead,
        name="appointment_cannot_go_ahead",
    ),
]
