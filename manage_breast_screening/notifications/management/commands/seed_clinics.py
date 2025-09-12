import json
import logging

from django.core.management.base import BaseCommand

from manage_breast_screening.notifications.models import Clinic

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command to seed Clinic data from the `clinic_data.json` file
    """

    def handle(self, *args, **kwargs):
        seed_file = open(
            "./manage_breast_screening/notifications/data/clinic_data.json"
        ).read()
        data = json.loads(seed_file)

        confirm = input(
            "You are about to update any existing Clinics with the current fixture file. Are you sure? (yes/no)"
        )
        if confirm.strip().lower() != "yes":
            self.stdout.write(self.style.ERROR("Cancelled."))
            return

        logger.info("Beginning seed_clinics command")

        for clinic in data:
            self.create_clinic(clinic)

    def create_clinic(self, clinic_data):
        clinic = Clinic.objects.filter(id=clinic_data["id"])
        if clinic.first() is None:
            logger.info(
                f"Creating Clinic with code {clinic_data['code']} and id {clinic_data['id']}"
            )

            Clinic.objects.create(**clinic_data)
        else:
            logger.info(
                f"Updating Clinic with code {clinic_data['code']} and id {clinic_data['id']}"
            )
            clinic.update(**clinic_data)
