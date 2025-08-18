from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_not_required
from django.db.models import Case, Q, When
from django.shortcuts import get_object_or_404, redirect, render

from .models import PERSONAS


@login_not_required
def persona_login(request):
    users = _get_users(request.user)

    if request.method == "POST":
        username = get_object_or_404(users, username=request.POST["username"])
        login(request, username)
        return redirect(_next_page(request))

    else:
        return render(
            request,
            "auth/persona_sign_in.jinja",
            context={
                "users": users,
                "page_title": "Personas",
                "current_user": request.user,
                "next": request.GET.get("next", request.path),
            },
        )


def _next_page(request):
    url = request.POST.get("next", "/")

    if not url.startswith("/"):
        return request.path

    return url


def _get_users(current_user):
    users = get_user_model().objects.filter(
        username__in=(persona.username for persona in PERSONAS)
    )

    if current_user:
        # Stick the current user at the top of the list
        return users.annotate(
            ordering=Case(When(Q(username=current_user.username), then=0), default=1)
        ).order_by("ordering", "first_name")

    return users.order_by("first_name")
