from django.apps import AppConfig


class MBSAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manage_breast_screening.auth"
    label = "mbs_auth"  # avoid collision with django.contrib.auth's app label "auth"
    verbose_name = "Authentication"
