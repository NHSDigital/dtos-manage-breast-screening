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
        views.ShowAppointment.as_view(),
        name="show_appointment",
    ),
    path(
        "<uuid:pk>/start-screening/",
        views.StartScreening.as_view(),
        name="start_screening",
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
        views.AwaitingImages.as_view(),
        name="awaiting_images",
    ),
    path(
        "<uuid:pk>/cannot-go-ahead/",
        views.AppointmentCannotGoAhead.as_view(),
        name="appointment_cannot_go_ahead",
    ),
    path(
        "<uuid:pk>/special-appointment/",
        views.ProvideSpecialAppointmentDetails.as_view(),
        name="provide_special_appointment_details",
    ),
    path(
        "<uuid:pk>/special-appointment/which-reasons/",
        views.MarkReasonsTemporary.as_view(),
        name="mark_reasons_temporary",
    ),
]
