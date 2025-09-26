from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.clinics.models import Provider, UserAssignment

from ...models import PERSONAS

User = get_user_model()


class Command(BaseCommand):
    """
    Create persona users for use in non-production environments
    """

    def handle(self, *args, **options):
        if not settings.PERSONAS_ENABLED:
            raise CommandError("PERSONAS_ENABLED=False. Refusing to create.")

        try:
            provider = Provider.objects.first()
            if not provider:
                raise CommandError("No providers found. Refusing to create.")
            for persona in PERSONAS:
                group = Group.objects.get(name=persona.group)
                user, _ = User.objects.get_or_create(
                    nhs_uid=persona.username,
                    defaults={
                        "first_name": persona.first_name,
                        "last_name": persona.last_name,
                    },
                )
                UserAssignment.objects.create(user=user, provider=provider)
                user.groups.add(group)
        except Exception as e:
            raise CommandError(e)
