from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path(
        "/message-status/create",
        views.create_message_status,
        name="create_message_status",
    ),
]
