from django.shortcuts import render
from django.views.decorators.http import require_GET


def permission_denied(request, exception):  # noqa: ARG001
    return render(request, "403.jinja", status=403)


@require_GET
def page_not_found(request, exception):  # noqa: ARG001
    return render(request, "404.jinja", status=404)


@require_GET
def server_error(request):
    return render(request, "500.jinja", status=500)
