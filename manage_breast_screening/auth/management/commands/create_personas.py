from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from ...models import PERSONAS

User = get_user_model()


class Command(BaseCommand):
    """
    Create persona users for use in non-production environments
    """

    def handle(self, *args, **options):
        try:
            for persona in PERSONAS:
                group = Group.objects.get(name=persona.group)
                user, _ = User.objects.get_or_create(
                    username=persona.username,
                    defaults={
                        "first_name": persona.first_name,
                        "last_name": persona.last_name,
                    },
                )
                user.groups.add(group)
        except Exception as e:
            raise CommandError(e)
