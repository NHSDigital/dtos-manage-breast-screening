from django.apps import AppConfig
from django_fsm.signals import post_transition


def post_transition_callback(sender, instance, *args, **kwargs):
    from .models.appointment import Appointment

    if sender is Appointment:
        instance.create_history_object()


class ParticipantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manage_breast_screening.participants"
    verbose_name = "Participants"

    def ready(self):
        post_transition.connect(post_transition_callback)
