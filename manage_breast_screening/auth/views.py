from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .oauth import get_cis2_client, jwk_from_public_key


@login_not_required
def sign_in(request):
    """Entry point for authentication with CIS2"""
    return render(
        request,
        "auth/sign_in.jinja",
        {
            "page_title": "Sign in",
            "navActive": "sign_in",
        },
    )


def sign_out(request):
    auth_logout(request)
    return redirect(reverse("home"))


@login_not_required
def cis2_sign_in(request):
    """Start the CIS2 OAuth2/OIDC authorization flow."""
    client = get_cis2_client()
    redirect_uri = request.build_absolute_uri(reverse("auth:cis2_callback")).rstrip("/")
    # The acr_values param determines which authentication options are available to the user
    # See https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/acr-values#acr-values
    return client.authorize_redirect(
        request, redirect_uri, acr_values="AAL2_OR_AAL3_ANY"
    )


@login_not_required
def cis2_callback(request):
    """Handle CIS2 OAuth2/OIDC callback, create/login the Django user, then redirect home."""
    client = get_cis2_client()
    token = client.authorize_access_token(request)
    userinfo = client.userinfo(token=token)
    sub = userinfo.get("sub")
    if not sub:
        return HttpResponseBadRequest("Missing subject in CIS2 response")

    User = get_user_model()
    defaults = {}
    if userinfo.get("email"):
        defaults["email"] = userinfo["email"]
    if userinfo.get("given_name"):
        defaults["first_name"] = userinfo["given_name"]
    if userinfo.get("family_name"):
        defaults["last_name"] = userinfo["family_name"]

    # Map CIS2 subject ('sub') to the built-in 'username' field, Django's
    # default unique identifier for users
    user, _ = User.objects.get_or_create(username=sub, defaults=defaults)
    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect(reverse("home"))


@login_not_required
def jwks(request):
    """Publish JSON Web Key Set (JWKS) with the public key used for private_key_jwt."""
    try:
        jwk = jwk_from_public_key()
        if not jwk:
            return JsonResponse({"keys": []})
        # Use the thumbprint as the KID
        kid = jwk.thumbprint()

        jwk_dict = jwk.as_dict()
        jwk_dict["kid"] = kid
        jwk_dict["use"] = "sig"
        jwk_dict["alg"] = "RS512"
        return JsonResponse({"keys": [jwk_dict]})
    except Exception:
        return JsonResponse({"keys": []})
