import json
import logging
import os
import subprocess
import time
from datetime import datetime
from tempfile import NamedTemporaryFile

from mesh_client import INT_ENDPOINT, MeshClient


def test_notifications():
    try:
        environment = os.getenv("ENVIRONMENT", "dev")
        pr_number = os.getenv("PR_NUMBER")

        if environment == "prod":
            return

        storage_account = f"stmanbrs{environment}uks"

        if pr_number is not None:
            environment = f"pr-{pr_number}"
            storage_account = f"stmanbrspr{pr_number}uks"

        logging.info("Running notifications smoke test")
        resource_group_name = f"rg-manbrs-{environment}-container-app-uks"
        containerapp_name = f"manbrs-web-{environment}"
        container_name = "notifications-reports"
        pattern = "SM0K3-*-report.csv"

        # Fetch MESH connection secrets and store in env
        populate_mesh_env_vars(resource_group_name, containerapp_name)

        # Add smoke test data DAT file to MESH inbox
        mesh_client().send_message(
            os.getenv("NBSS_MESH_INBOX_NAME"),
            smoke_test_data().encode("ASCII"),
            subject="Smoke test data",
        )

        # Execute container app jobs:
        # smm: Store MESH messages - Move the DAT file from MESH to blob storage.
        # cap: Create Appointments - Read today's files from blob storage and create
        #      Clinic and Appointment records for them.
        # smb: Send Message Batch - Send messages for today's Appointment records.
        # smk: Create smoke test report - Create and export report to blob storage.
        for job in ["smm", "cap", "smb", "smk"]:
            logging.info(f"Running container app job manbrs-{job}-{environment}")
            job_result = subprocess.run(
                [f"{working_dir()}/run_container_app_job.sh", environment, job],
                capture_output=True,
                text=True,
            )
            assert job_result.returncode == 0

        # Download report
        download_result = subprocess.run(
            azure_storage_blob_download_reports_command(
                container_name, storage_account, pattern
            ),
            capture_output=True,
            text=True,
        )
        assert download_result.returncode == 0

        report_filename = "SM0K3-reconciliation-report.csv"

        assert report_filename in download_result.stdout

        report_contents = open(f"{working_dir()}/{report_filename}").read()
        assert "SM0K3" in report_contents

        logging.info("Finished notifications smoke test")
    finally:
        # Delete smoke test generated report
        subprocess.run(
            azure_storage_blob_delete_reports_command(
                container_name, storage_account, pattern
            )
        )


def azure_storage_blob_download_reports_command(
    container_name, storage_account, pattern
) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "download-batch",
        "--destination",
        working_dir(),
        "--source",
        container_name,
        "--pattern",
        pattern,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def azure_storage_blob_delete_reports_command(
    container_name, storage_account, pattern
) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "delete-batch",
        "--source",
        container_name,
        "--pattern",
        pattern,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def populate_mesh_env_vars(resource_group: str, containerapp_name: str):
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


def working_dir() -> str:
    return os.path.dirname(os.path.realpath(__file__))


def smoke_test_data() -> str:
    data = open(f"{working_dir()}/smoke_test_data.dat").read()
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
