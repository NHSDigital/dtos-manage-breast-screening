import glob
import logging
import os
import subprocess
from datetime import datetime


def test_notifications():
    try:
        environment = os.getenv("ENVIRONMENT", "dev")

        if environment == "prod":
            return

        logging.info("Running notifications smoke test")
        today_formatted = datetime.now().strftime("%Y-%m-%d")
        blob_data = smoke_test_data()
        storage_account = f"stmanbrs{environment}uks"
        container_name = "notifications-mesh-data"
        report_container_name = "notifications-smoke-test-reports"
        blob_name = f"{today_formatted}/smoke_test.dat"

        # Upload smoke test data DAT file
        upload_result = subprocess.run(
            azure_storage_blob_upload_command(
                blob_name, blob_data, container_name, storage_account
            )
        )
        assert upload_result.returncode == 0

        # Execute container app jobs
        for job in ["cap", "smb", "crp"]:
            logging.info(f"Running container app job manbrs-{job}-{environment}")
            job_result = subprocess.run(
                [f"{working_dir()}/run_container_app_job.sh", environment, job]
            )
            assert job_result.returncode == 0

        # Download report
        download_result = subprocess.run(
            azure_storage_blob_download_command(report_container_name, storage_account)
        )
        assert download_result.returncode == 0

        report_files = glob.glob(f"{working_dir()}/*reconciliation-report.csv")
        assert len(report_files) == 1

        report_content = open(report_files[0]).read()

        assert "SM0K3" in report_content

        logging.info("Finished notifications smoke test")
    finally:
        # Delete smoke test data
        subprocess.run(
            azure_storage_blob_delete_command(
                blob_name, container_name, storage_account
            )
        )
        # Delete smoke test generated report
        subprocess.run(
            azure_storage_blob_delete_reports_command(
                report_container_name, storage_account
            )
        )


def azure_storage_blob_upload_command(
    blob_name, blob_data, container_name, storage_account
) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "upload",
        "-n",
        blob_name,
        "-c",
        container_name,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
        "--overwrite",
        "true",
        "--data",
        blob_data,
    ]


def azure_storage_blob_delete_command(
    blob_name, container_name, storage_account
) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "delete",
        "-n",
        blob_name,
        "-c",
        container_name,
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def azure_storage_blob_delete_reports_command(
    container_name, storage_account
) -> list[str]:
    return [
        "az",
        "storage",
        "blob",
        "delete-batch",
        "--source",
        container_name,
        "--pattern",
        "*.csv",
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def azure_storage_blob_download_command(container_name, storage_account) -> list[str]:
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
        "*.csv",
        "--account-name",
        storage_account,
        "--auth-mode",
        "login",
    ]


def working_dir() -> str:
    return os.path.dirname(os.path.realpath(__file__))


def smoke_test_data() -> str:
    data = open(f"{working_dir()}/smoke_test_data.dat").read()
    return data.replace("20250101", datetime.now().strftime("%Y%m%d"))
