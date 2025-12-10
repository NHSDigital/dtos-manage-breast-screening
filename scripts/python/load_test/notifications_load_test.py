import logging
import os
import subprocess
import time
from datetime import datetime

from manage_breast_screening.notifications.models import (
    Appointment,
    Clinic,
)
from scripts.python.smoke_test.notifications_smoke_test import (
    mesh_client,
    populate_mesh_env_vars,
)

WORK_DIR = os.path.dirname(os.path.realpath(__file__))
STARTUP_SCRIPT_PATH = f"{WORK_DIR}/../../bash/run_container_app_job.sh"
NUMBER_OF_ROWS = os.getenv("NUMBER_OF_ROWS", "5")
NUMBER_OF_FILES = os.getenv("NUMBER_OF_ROWS", "5")


def test_load():
    logging.info("Running notifications load test")

    environment = os.getenv("ENVIRONMENT")
    resource_group_name = f"rg-manbrs-{environment}-container-app-uks"

    if environment == "prod":
        return

    add_load_test_data_to_mesh(environment, resource_group_name)

    for job in ["smm", "cap"]:
        logging.info(
            "Starting notifications container app job manbrs-%s-%s", job, environment
        )

        job_result = subprocess.run(
            [STARTUP_SCRIPT_PATH, environment, job],
            check=True,
            capture_output=True,
            text=True,
        )
        assert job_result.returncode == 0

    logging.info("Finished notifications load test")


def add_load_test_data_to_mesh(environment: str, resource_group_name: str):
    populate_mesh_env_vars(environment, resource_group_name)
    for number in range(int(NUMBER_OF_FILES)):
        logging.info(f"sending mesh message {number}")
        mesh_client().send_message(
            os.getenv("NBSS_MESH_INBOX_NAME"),
            generate_load_test_data(number).encode("ASCII"),
            subject="Load test data",
        )


def generate_load_test_data(file_sequence_number: int) -> str:
    data = open(f"{WORK_DIR}/load_test_data.dat").read()
    data = data.replace("20250101", datetime.now().strftime("%Y%m%d"))
    data = data.replace("88888888", f"{file_sequence_number:06d}")
    first_appointment_id = f"L04D-1-{time.time_ns()}"
    data = data.replace("L04D-0000000000", first_appointment_id)

    rows = data.split("\n")
    _header = rows[0]
    _footer = rows[3]
    first_data_row = rows[2]

    for number in range(2, int(NUMBER_OF_ROWS)):
        # logging.info(f"creating row {number}")
        new_data = first_data_row.replace("000001", f"{number:06d}")
        new_data = new_data.replace(
            first_appointment_id, f"L04D-{number}-{time.time_ns()}"
        )
        rows.insert((number + 1), new_data)

    return "\n".join(rows)


def delete_all_load_test_data():
    # You can run this in a python shell in the AVD, put the following in after exec into web app:
    # python manage.py shell
    # from manage_breast_screening.notifications.models import (
    #     Appointment,
    #     Clinic,
    # )
    appt_count = Appointment.objects.filter(nbss_id__contains="L04D").count()
    Appointment.objects.filter(nbss_id__contains="L04D").delete()
    logging.info("deleting %s appointments", appt_count)
    clinic_count = Clinic.objects.filter(bso_code__contains="L04D").count()
    logging.info("deleting %s clinics", clinic_count)
    Clinic.objects.filter(bso_code__contains="L04D").delete()
