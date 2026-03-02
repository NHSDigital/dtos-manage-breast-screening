from django.shortcuts import render


def permission_denied(request, exception):  # noqa: ARG001
    return render(request, "403.jinja", status=403)
