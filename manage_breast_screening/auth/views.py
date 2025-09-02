import logging

from authlib.jose import JoseError, jwt
from authlib.jose.errors import ExpiredTokenError, InvalidClaimError, InvalidTokenError
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required
from django.contrib.sessions.models import Session
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .oauth import get_cis2_client, jwk_from_public_key


@login_not_required
def login(request):
    """Entry point for authentication with CIS2"""
    return render(
        request,
        "auth/login.jinja",
        {
            "page_title": "Log in",
        },
    )


def logout(request):
    auth_logout(request)
    return redirect(reverse("home"))


@login_not_required
def cis2_login(request):
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
    sub = userinfo.get("sub")  # Unique identifier for the user in CIS2
    if not sub:
        return HttpResponseBadRequest("Missing subject in CIS2 response")

    User = get_user_model()
    defaults = {}
    defaults["email"] = userinfo["email"]
    defaults["first_name"] = userinfo["given_name"]
    defaults["last_name"] = userinfo["family_name"]

    user, _ = User.objects.update_or_create(username=sub, defaults=defaults)
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


@require_http_methods(["POST"])
@csrf_exempt
@login_not_required
def cis2_back_channel_logout(request):
    """Handle CIS2 back-channel logout notifications.

    This endpoint receives logout tokens from CIS2 when a user's session is terminated.
    See: https://openid.net/specs/openid-connect-backchannel-1_0.html
    See: https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/session-management#back-channel-logout
    """
    logout_token = request.POST.get("logout_token")
    if not logout_token:
        return HttpResponseBadRequest("Missing logout_token")

    # Get the CIS2 client and prepare key loader for token verification
    client = get_cis2_client()
    metadata = client.load_server_metadata()
    key_loader = client.create_load_key()
    try:
        verification_rules = {
            "iss": {"values": [metadata["issuer"]], "essential": True},
            "aud": {"values": [client.client_id], "essential": True},
            "exp": {"essential": True},
            "iat": {"essential": True},
            "events": {
                "essential": True,
                "validate": lambda claim, value: isinstance(value, dict)
                and "http://schemas.openid.net/event/backchannel-logout" in value,
            },
            "nonce": {"validate": lambda claim, value: value is None},
        }
        claims = jwt.decode(
            logout_token,
            key=key_loader,
            claims_options=verification_rules,
        )
        claims.validate(leeway=60)
    except (JoseError, InvalidClaimError, ExpiredTokenError, InvalidTokenError) as e:
        logging.error(f"Invalid logout token: {str(e)}")
        return HttpResponseBadRequest("Invalid logout token")

    if "sub" not in claims:
        return HttpResponseBadRequest("Invalid logout token: Missing 'sub' claim")

    # CIS2 also sends a sid claim identifying the session being terminated. For
    # simplicity, we ignore that for now and look up the user by the sub claim
    # (a uid in CIS2) before invalidating all of their sessions.
    User = get_user_model()
    try:
        user = User.objects.get(username=claims["sub"])
    except User.DoesNotExist:
        # Nothing to do if the user doesn't exist locally
        return JsonResponse({"status": "ok"})
    # TODO: replace with something better, this looks through all unexpired sessions
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if str(data.get("_auth_user_id")) == str(user.pk):
            session.delete()

    return JsonResponse({"status": "ok"})
