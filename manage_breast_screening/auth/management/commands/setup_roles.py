from django.core.management.base import BaseCommand

from ...roles import setup_roles


class Command(BaseCommand):
    """
    Setup the groups and permissions for the different roles.
    """

    def handle(self, *args, **options):
        setup_roles()
