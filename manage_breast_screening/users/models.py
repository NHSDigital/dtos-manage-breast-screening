from functools import cached_property

import rules
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.crypto import salted_hmac


class UserManager(BaseUserManager):
    def create_user(self, nhs_uid, email="", **extra_fields):
        if not nhs_uid:
            raise ValueError("The NHS UID must be set")
        user = self.model(nhs_uid=nhs_uid, email=email or "", **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    nhs_uid = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(
        default=False,
        help_text="Grants access to system-wide settings across all providers.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "nhs_uid"
    REQUIRED_FIELDS = []

    @cached_property
    def _current_provider_roles(self):
        if not self.current_provider:
            return []
        assignment = self.assignments.filter(provider=self.current_provider).first()
        return assignment.roles if assignment else []

    def has_role(self, role):
        return role in self._current_provider_roles

    @property
    def current_provider(self):
        """
        The provider that the user is currently logged into.
        This should be set by CurrentProviderMiddleware
        """
        try:
            return self._current_provider
        except AttributeError:
            return None

    @current_provider.setter
    def current_provider(self, provider):
        self._current_provider = provider

    def get_session_auth_hash(self):
        """
        Override this method in AbstractBaseUser. It's purpose is to invalidate
        the session hash on password changes. Given we don't use locally stored
        passwords for authentication, here we simply hash the is_active field.
        """
        key_salt = "manage_breast_screening.users.models.User.get_session_auth_hash"
        return salted_hmac(
            key_salt, str(self.is_active), algorithm="sha256"
        ).hexdigest()

    @property
    def access_labels(self):
        labels = list(
            {role for assignment in self.assignments.all() for role in assignment.roles}
        )
        if self.is_superuser:
            labels.append("Sysadmin")
        return labels

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name[0] + ". " + self.last_name

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        return rules.has_perm(perm, self, obj) or self.is_superuser

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj=obj) for perm in perm_list)

    def has_module_perms(self, package_name, obj=None):
        """
        Check permissions at a module level, instead of using granular permissions.

        This is required to use Django admin.
        """
        return self.has_perm(package_name) or self.is_superuser
