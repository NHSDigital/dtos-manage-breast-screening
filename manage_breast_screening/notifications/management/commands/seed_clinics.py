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
            "You are about to update any existing Clinics with the location_description and location_url from the current fixture file. Are you sure? (yes/no)"
        )
        if confirm.strip().lower() != "yes":
            self.stdout.write(self.style.ERROR("Cancelled."))
            return

        logger.info("Beginning seed_clinics command")

        for clinic in data:
            self.create_clinic(clinic)

    def create_clinic(self, clinic_data):
        clinic = Clinic.objects.filter(
            code=clinic_data["code"], bso_code=clinic_data["bso_code"]
        )
        if clinic.first() is None:
            Clinic.objects.create(**clinic_data)
            logger.info(
                f"Created Clinic with code {clinic_data['code']} and id {clinic_data['id']}"
            )
        else:
            clinic.update(
                location_description=clinic_data["location_description"],
                location_url=clinic_data["location_url"],
            )
            logger.info(
                f"Updated Clinic with code {clinic_data['code']} and id {clinic_data['id']}"
            )
