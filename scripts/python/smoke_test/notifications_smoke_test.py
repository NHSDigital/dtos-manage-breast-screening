import json
import logging
import os
import subprocess
import time
from datetime import datetime
from tempfile import NamedTemporaryFile

from mesh_client import INT_ENDPOINT, MeshClient

CONTAINER_NAME = "notifications-reports"
REPORT_FILENAME = "SM0K3-reconciliation-report.csv"
WORK_DIR = os.path.dirname(os.path.realpath(__file__))
STARTUP_SCRIPT_PATH = f"{WORK_DIR}/../../bash/run_container_app_job.sh"


def test_notifications():
    try:
        logging.info("Running notifications smoke test")

        environment, storage_account, resource_group_name = configure()

        if environment == "prod":
            return

        setup_mesh_inbox_test_data(environment, resource_group_name)

        for job in ["smm", "cap", "smb", "smk"]:
            job_result = run_subprocess(
                f"Starting notifications container app job manbrs-{job}-{environment}",
                [STARTUP_SCRIPT_PATH, environment, job],
            )
            assert job_result.returncode == 0

        download_result = run_subprocess(
            "Downloading generated smoke test report from blob storage",
            azure_storage_blob_download_reports_command(storage_account),
        )
        assert download_result.returncode == 0
        assert REPORT_FILENAME in download_result.stdout

        report_contents = open(f"{WORK_DIR}/{REPORT_FILENAME}").read()
        assert "SM0K3" in report_contents

        logging.info("Finished notifications smoke test")
    finally:
        run_subprocess(
            "Deleting generated smoke test report from blob storage",
            azure_storage_blob_delete_reports_command(storage_account),
        )


def configure():
    environment = os.getenv("ENVIRONMENT", "dev")
    pr_number = os.getenv("PR_NUMBER", "")
    storage_account = f"stmanbrs{environment}uks"

    if pr_number != "":
        environment = f"pr-{pr_number}"
        storage_account = f"stmanbrspr{pr_number}uks"

    resource_group_name = f"rg-manbrs-{environment}-container-app-uks"

    return (environment, storage_account, resource_group_name)


def run_subprocess(description: str, command: list[str]):
    logging.info(description)
    return subprocess.run(command, capture_output=True, text=True)


def azure_storage_blob_download_reports_command(storage_account: str) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "download-batch",
        "--destination",
        WORK_DIR,
        "--source",
        CONTAINER_NAME,
        "--pattern",
        REPORT_FILENAME,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def azure_storage_blob_delete_reports_command(storage_account: str) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "delete-batch",
        "--source",
        CONTAINER_NAME,
        "--pattern",
        REPORT_FILENAME,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


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
    data = open(f"{WORK_DIR}/smoke_test_data.dat").read()
    data = data.replace("20250101", datetime.now().strftime("%Y%m%d"))
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
