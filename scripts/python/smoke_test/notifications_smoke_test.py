import json
import logging
import os
import subprocess
import time
from datetime import datetime
from tempfile import NamedTemporaryFile

from mesh_client import INT_ENDPOINT, MeshClient

WORK_DIR = os.path.dirname(os.path.realpath(__file__))
STARTUP_SCRIPT_PATH = f"{WORK_DIR}/../../bash/run_container_app_job.sh"


def test_notifications():
    logging.info("Running notifications smoke test")

    environment = os.getenv("ENVIRONMENT")
    resource_group_name = f"rg-manbrs-{environment}-container-app-uks"

    if environment == "prod":
        return

    setup_mesh_inbox_test_data(environment, resource_group_name)

    for job in ["smm", "cap", "smb", "smk"]:
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

    logging.info("Finished notifications smoke test")


def setup_mesh_inbox_test_data(environment: str, resource_group_name: str):
    populate_mesh_env_vars(environment, resource_group_name)
    mesh_client().send_message(
        os.getenv("NBSS_MESH_INBOX_NAME"),
        smoke_test_data().encode("ASCII"),
        subject="Smoke test data",
    )


def populate_mesh_env_vars(environment: str, resource_group: str):
    containerapp_name = f"manbrs-web-{environment}"
    secret_names = [
        "NBSS-MESH-INBOX-NAME",
        "NBSS-MESH-PASSWORD",
        "NBSS-MESH-CERT",
        "NBSS-MESH-PRIVATE-KEY",
    ]
    for secret_name in secret_names:
        populate_env_secret_from_azure_containerapp(
            resource_group, containerapp_name, secret_name
        )


def populate_env_secret_from_azure_containerapp(
    resource_group_name: str, containerapp_name: str, secret_name: str
):
    process_result = subprocess.run(
        [
            "az",
            "containerapp",
            "secret",
            "show",
            "--secret-name",
            secret_name,
            "-g",
            resource_group_name,
            "-n",
            containerapp_name,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert process_result.returncode == 0

    env_var_name = secret_name.replace("-", "_")
    data = json.loads(process_result.stdout)
    os.environ[env_var_name] = data["value"]


def smoke_test_data() -> str:
    minutes_since_epoch = int(time.time() / 60)
    data = open(f"{WORK_DIR}/smoke_test_data.dat").read()
    data = data.replace("20250101", datetime.now().strftime("%Y%m%d"))
    data = data.replace("88888888", str(minutes_since_epoch))
    return data.replace("SM0K3-0000000000", f"SM0K3-{time.time_ns()}")


def mesh_client() -> MeshClient:
    client = MeshClient(
        INT_ENDPOINT,
        os.getenv("NBSS_MESH_INBOX_NAME"),
        os.getenv("NBSS_MESH_PASSWORD"),
        cert=(
            tmp_file(os.getenv("NBSS_MESH_CERT")).name,
            tmp_file(os.getenv("NBSS_MESH_PRIVATE_KEY")).name,
        ),
    )
    client.handshake()
    return client


def tmp_file(content: str) -> NamedTemporaryFile:
    file = NamedTemporaryFile(delete=False)
    file.write(content.encode("utf-8"))

    return file
