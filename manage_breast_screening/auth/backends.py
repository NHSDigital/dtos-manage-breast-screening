import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class CIS2Backend:
    """
    Custom authentication backend for CIS2 OAuth/OIDC flow.
    """

    def authenticate(self, _request, cis2_sub=None, cis2_userinfo=None, **_kwargs):
        """
        CIS2 authentication happens via the CIS2 auth service. Here we simply
        update or create the user based on the CIS2 userinfo response.
        """
        if cis2_sub is None or cis2_userinfo is None:
            return None

        User = get_user_model()
        defaults = {}

        for db_field, userinfo_field in [
            ("email", "email"),
            ("first_name", "given_name"),
            ("last_name", "family_name"),
        ]:
            value = cis2_userinfo.get(userinfo_field, "")
            if value:
                defaults[db_field] = value
            else:
                logger.warning(
                    f"Missing or empty {userinfo_field} in CIS2 userinfo response"
                )

        user, _ = User.objects.update_or_create(nhs_uid=cis2_sub, defaults=defaults)
        return user

    def get_user(self, user_id):
        """
        Retrieve a user by their primary key.
        Called by Django's session middleware on every request.
        Returns None if the user doesn't exist or is inactive.
        """
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
            return user if user.is_active else None
        except User.DoesNotExist:
            return None
