"""
Django management command to poll MESH inbox and store messages in Azure Blob Storage
"""

from django.core.management.base import BaseCommand

from manage_breast_screening.notifications.mesh.polling import run_mesh_polling


class Command(BaseCommand):
    help = "Poll MESH sandbox inbox and store messages in Azure Blob Storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode (don't actually store to Azure)",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Starting MESH inbox polling process in DRY-RUN mode..."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Starting MESH inbox polling process...")
            )

        try:
            run_mesh_polling(dry_run=dry_run)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "MESH inbox polling completed successfully (DRY-RUN)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("MESH inbox polling completed successfully")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"MESH inbox polling failed: {e}"))
            raise
