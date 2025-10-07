from urllib.parse import urlencode

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_not_required
from django.db.models import Case, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from manage_breast_screening.core.utils.urls import extract_next_path_from_params

from .models import PERSONAS


@login_not_required
def persona_login(request):
    users = _get_users(request.user)
    next_path = extract_next_path_from_params(request)

    if request.method == "POST":
        user = get_object_or_404(users, nhs_uid=request.POST["username"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        redirect_url = reverse("clinics:select_provider")
        if next_path:
            redirect_url = f"{redirect_url}?{urlencode({'next': next_path})}"

        return redirect(redirect_url)
    else:
        return render(
            request,
            "auth/persona_login.jinja",
            context={
                "users": users,
                "page_title": "Personas",
                "current_user": request.user,
                "next": next_path,
            },
        )


def _get_users(current_user):
    users = get_user_model().objects.filter(
        nhs_uid__in=(persona.username for persona in PERSONAS)
    )

    if current_user.is_authenticated:
        # Stick the current user at the top of the list
        return users.annotate(
            ordering=Case(When(Q(nhs_uid=current_user.nhs_uid), then=0), default=1)
        ).order_by("ordering", "first_name")

    return users.order_by("first_name")
