import rules
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.crypto import salted_hmac


class UserManager(BaseUserManager):
    def create_user(self, nhs_uid, email=None, **extra_fields):
        if not nhs_uid:
            raise ValueError("The NHS UID must be set")
        user = self.model(nhs_uid=nhs_uid, email=email, **extra_fields)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "nhs_uid"
    REQUIRED_FIELDS = []

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

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        return rules.has_perm(perm, self, obj)

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj=obj) for perm in perm_list)
