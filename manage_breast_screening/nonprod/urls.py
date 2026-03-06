from django.urls import path
from django.views.generic import TemplateView

from manage_breast_screening.core.views.errors import page_not_found, server_error

app_name = "nonprod"

urlpatterns = [
    path(
        "components/",
        TemplateView.as_view(template_name="nonprod/components.jinja"),
    ),
    path("debug/404/", lambda request: page_not_found(request, None)),
    path("debug/500/", server_error),
]
