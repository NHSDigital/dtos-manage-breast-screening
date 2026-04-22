from django.urls import path

from . import views

app_name = "reading"

urlpatterns = [
    path("", views.show_reading_dashboard_view, name="show_reading_dashboard"),
    path(
        "sessions/<uuid:session_pk>/reads/<uuid:pk>/",
        views.ReadImageView.as_view(),
        name="image_read",
    ),
]
