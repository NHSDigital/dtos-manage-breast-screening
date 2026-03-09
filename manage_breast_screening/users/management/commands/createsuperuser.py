from django.core.management.base import BaseCommand

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.users.models import User


class Command(BaseCommand):
    help = "Create a superuser with no usable password"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--nhs-uid", required=True)
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)

    def handle(self, *args, **options):
        u = User.objects.create_user(
            email=options["email"],
            nhs_uid=options["nhs_uid"],
            first_name=options["first_name"],
            last_name=options["last_name"],
            is_superuser=True,
            is_staff=True,
        )
        Auditor(system_update_id="create_superuser").audit_create(u)
        self.stdout.write(f"Superuser {u.email} created.")
