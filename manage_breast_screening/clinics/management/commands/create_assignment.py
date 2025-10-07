import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics.models import Provider, UserAssignment

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Create a user assignment to a provider"

    def handle(self, *args, **options):
        try:
            users = User.objects.all().order_by("first_name", "last_name")
            providers = Provider.objects.all().order_by("name")

            if not users.exists():
                self.stdout.write(self.style.ERROR("No users found in the database."))
                return

            if not providers.exists():
                self.stdout.write(
                    self.style.ERROR("No providers found in the database.")
                )
                return

            self.stdout.write("\nAvailable users:")
            for i, user in enumerate(users, 1):
                full_name = user.get_full_name() or "No name set"
                self.stdout.write(f"{i}. {full_name} ({user.nhs_uid})")

            while True:
                try:
                    user_choice = input("\nSelect a user (enter number): ").strip()
                    user_index = int(user_choice) - 1
                    if 0 <= user_index < len(users):
                        selected_user = users[user_index]
                        break
                    else:
                        self.stdout.write(
                            self.style.ERROR("Invalid selection. Please try again.")
                        )
                except (ValueError, KeyboardInterrupt):
                    self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                    return

            self.stdout.write("\nAvailable providers:")
            for i, provider in enumerate(providers, 1):
                self.stdout.write(f"{i}. {provider.name}")

            while True:
                try:
                    provider_choice = input(
                        "\nSelect a provider (enter number): "
                    ).strip()
                    provider_index = int(provider_choice) - 1
                    if 0 <= provider_index < len(providers):
                        selected_provider = providers[provider_index]
                        break
                    else:
                        self.stdout.write(
                            self.style.ERROR("Invalid selection. Please try again.")
                        )
                except (ValueError, KeyboardInterrupt):
                    self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                    return

            roles = list(Role)
            self.stdout.write("\nAvailable roles:")
            for i, role in enumerate(roles, 1):
                self.stdout.write(f"{i}. {role.value}")

            while True:
                try:
                    role_choice = input("\nSelect a role (enter number): ").strip()
                    role_index = int(role_choice) - 1
                    if 0 <= role_index < len(roles):
                        selected_role = roles[role_index]
                        break
                    else:
                        self.stdout.write(
                            self.style.ERROR("Invalid selection. Please try again.")
                        )
                except (ValueError, KeyboardInterrupt):
                    self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                    return

            try:
                assignment = UserAssignment.objects.create(
                    user=selected_user,
                    provider=selected_provider,
                    roles=[selected_role.value],
                )

                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created assignment: {assignment}")
                )

            except IntegrityError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Assignment already exists between {selected_user.get_full_name()} "
                        f"and {selected_provider.name}"
                    )
                )

        except Exception as e:
            logger.exception("Error creating user assignment")
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
