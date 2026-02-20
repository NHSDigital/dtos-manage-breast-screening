import logging

from authlib.integrations.base_client.errors import MismatchingStateError, OAuthError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from manage_breast_screening.core.decorators import (
    basic_auth_exempt,
    current_provider_exempt,
)

from .oauth import cis2_redirect_uri, get_cis2_client, jwk_from_public_key
from .services import InvalidLogoutToken, decode_logout_token

logger = logging.getLogger(__name__)


@current_provider_exempt
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


@current_provider_exempt
def logout(request):
    auth_logout(request)
    return redirect(reverse("home"))


@current_provider_exempt
@login_not_required
def cis2_login(request):
    """Start the CIS2 OAuth2/OIDC authorization flow."""
    client = get_cis2_client()
    redirect_uri = cis2_redirect_uri()
    # The acr_values param determines which authentication options are available to the user
    # See https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/acr-values#acr-values
    return client.authorize_redirect(
        request, redirect_uri, acr_values=settings.CIS2_ACR_VALUES
    )


@current_provider_exempt
@login_not_required
def cis2_callback(request):
    """Handle CIS2 OAuth2/OIDC callback, create/login the Django user, then redirect home."""
    client = get_cis2_client()
    try:
        token = client.authorize_access_token(request)
    except MismatchingStateError:
        logger.exception("CIS2 callback failed: OAuth state mismatch")
        messages.warning(request, "Your login session expired. Please try again.")
        return redirect(reverse("auth:login"))
    except OAuthError:
        logger.exception("CIS2 callback failed: OAuth error")
        messages.warning(request, "There was a problem logging in. Please try again.")
        return redirect(reverse("auth:login"))

    id_token_userinfo = token.get("userinfo")
    userinfo = client.userinfo(token=token)

    # Validate sub claim in ID token matches sub claim at userinfo endpoint
    sub = userinfo.get("sub")
    if error := _validate_subject_claims(id_token_userinfo.get("sub"), sub):
        return HttpResponseBadRequest(error)

    # Validate assurance levels
    if error := _validate_id_assurance_level(
        id_token_userinfo.get("id_assurance_level")
    ):
        return HttpResponseForbidden(error)
    if error := _validate_authentication_assurance_level(
        id_token_userinfo.get("authentication_assurance_level")
    ):
        return HttpResponseForbidden(error)

    # Create/update the authenticated user
    user = authenticate(request, cis2_sub=sub, cis2_userinfo=userinfo)
    if not user:
        return HttpResponseServerError(
            "Failed to create/update authenticated CIS2 user"
        )

    auth_login(request, user)

    # Initialize session timeout tracking
    now = timezone.now()
    request.session["login_time"] = now.isoformat()
    request.session["last_activity"] = now.isoformat()

    return redirect(reverse("clinics:select_provider"))


@current_provider_exempt
@basic_auth_exempt
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
        logger.exception("Failed to build JWKS response")
        return JsonResponse({"keys": []}, status=500)


@current_provider_exempt
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
        claims = decode_logout_token(metadata["issuer"], key_loader, logout_token)
    except InvalidLogoutToken:
        return HttpResponseBadRequest("Invalid logout token")

    if "sub" not in claims:
        return HttpResponseBadRequest("Invalid logout token: Missing 'sub' claim")

    # CIS2 also sends a sid claim identifying the session being terminated. For
    # simplicity, we ignore that for now and look up the user by the sub claim
    # (a uid in CIS2) before invalidating all of their sessions.
    User = get_user_model()
    try:
        user = User.objects.get(nhs_uid=claims["sub"])
    except User.DoesNotExist:
        # Nothing to do if the user doesn't exist locally
        return JsonResponse({"status": "ok"})
    # Invalidate all sessions for this user
    user.session_set.all().delete()

    return JsonResponse({"status": "ok"})


def _validate_id_assurance_level(level: int | str | None) -> str | None:
    if level is not None:
        level = int(level)

    if level is None or level < settings.CIS2_REQUIRED_ID_ASSURANCE_LEVEL:
        logger.warning(
            f"CIS2 authentication rejected: id_assurance_level={level}, expected >= {settings.CIS2_REQUIRED_ID_ASSURANCE_LEVEL}"
        )
        return "Insufficient identity assurance level"
    return None


def _validate_authentication_assurance_level(level: int | str | None) -> str | None:
    level = int(level) if level is not None else level
    minimum_level = 2 if settings.CIS2_ACR_VALUES == "AAL2_OR_AAL3_ANY" else 3

    if level is None or level < minimum_level:
        logger.warning(
            f"CIS2 authentication rejected: authentication_assurance_level={level}, expected >= {minimum_level}"
        )
        return "Insufficient authentication assurance level"
    return None


def _validate_subject_claims(
    id_token_sub: str | None, userinfo_sub: str | None
) -> str | None:
    if not userinfo_sub:
        return "Missing subject in CIS2 response"
    if not id_token_sub:
        return "Missing subject in CIS2 ID token"
    if userinfo_sub != id_token_sub:
        return "Subject mismatch in CIS2 response"
    return None
