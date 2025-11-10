import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.clinics.models import Provider, UserAssignment

from ...models import PERSONAS

User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create persona users for use in non-production environments
    """

    def handle(self, *args, **options):
        if not settings.PERSONAS_ENABLED:
            logger.info("PERSONAS_ENABLED=False. Skipping persona creation.")
            return

        try:
            provider = Provider.objects.first()
            if not provider:
                raise CommandError("No providers found. Refusing to create.")
            for persona in PERSONAS:
                user, _ = User.objects.get_or_create(
                    nhs_uid=persona.username,
                    defaults={
                        "first_name": persona.first_name,
                        "last_name": persona.last_name,
                    },
                )
                UserAssignment.objects.create(
                    user=user, provider=provider, roles=[persona.role.value]
                )
        except Exception as e:
            raise CommandError(e)
