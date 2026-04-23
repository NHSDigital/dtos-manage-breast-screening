from django.urls import path

from . import views

app_name = "reading"

urlpatterns = [
    path("", views.show_reading_dashboard, name="show_reading_dashboard"),
]
