from collections import OrderedDict
from urllib.parse import urlencode

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)

from .models import PERSONAS


@csrf_exempt
@login_not_required
def persona_login(request):
    next_path = extract_relative_redirect_url(request, parameter_name="next")

    if request.method == "POST":
        try:
            user = get_user_model().objects.get(nhs_uid=request.POST["username"])
        except get_user_model().DoesNotExist:
            raise Http404("User not found")
        login(
            request, user, backend="manage_breast_screening.auth.backends.CIS2Backend"
        )

        now = timezone.now()
        request.session["login_time"] = now.isoformat()

        redirect_url = reverse("clinics:select_provider")
        if next_path:
            redirect_url = f"{redirect_url}?{urlencode({'next': next_path})}"

        return redirect(redirect_url)
    else:
        return render(
            request,
            "auth/persona_login.jinja",
            context={
                "providers_with_users": _get_providers_with_users(request.user),
                "sysadmin_users": _get_sysadmin_users(request.user),
                "page_title": "Persona logins",
                "next": next_path,
            },
        )


def _persona_users(current_user):
    persona_usernames = [persona.username for persona in PERSONAS]
    return (
        get_user_model()
        .objects.filter(nhs_uid__in=persona_usernames)
        .prefetch_related("assignments__provider")
        .order_by("first_name")
    )


def _user_entry(user, current_user):
    return {
        "user": user,
        "is_current": current_user.is_authenticated
        and user.nhs_uid == current_user.nhs_uid,
    }


def _get_providers_with_users(current_user):
    providers = OrderedDict()
    for user in _persona_users(current_user).filter(is_sysadmin=False):
        entry = _user_entry(user, current_user)
        for assignment in user.assignments.all():
            provider = assignment.provider
            if provider.pk not in providers:
                providers[provider.pk] = {"provider": provider, "roles": OrderedDict()}

            for role in sorted(assignment.roles):
                if role not in providers[provider.pk]["roles"]:
                    providers[provider.pk]["roles"][role] = []
                providers[provider.pk]["roles"][role].append(entry)

    return OrderedDict(
        sorted(providers.items(), key=lambda item: item[1]["provider"].name)
    ).values()


def _get_sysadmin_users(current_user):
    return [
        _user_entry(user, current_user)
        for user in _persona_users(current_user)
        if user.is_sysadmin
    ]
