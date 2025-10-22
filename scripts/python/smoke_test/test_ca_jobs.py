import subprocess
from datetime import datetime

import pytest


def pytest_addoption(parser):
    parser.addoption("--environment", action="store")


@pytest.fixture(scope="session")
def environment(request):
    environment_value = request.config.option.environment

    if environment_value is None:
        environment_value = "dev"

    if environment_value == "prod":
        pytest.skip()

    return environment_value


def test_nbss_data_pipeline(environment):
    data = smoke_test_data()

    acct = f"stmanbrs{environment}uks"
    data_container = "notifications-mesh-data"
    today_formatted = datetime.now().strftime("%Y-%m-%d")
    blob_name = f"{today_formatted}.smoke_test.dat"
    upload_cmd = f"az storage blob upload --data {data} -c {data_container} -n {blob_name} --account-name {acct}"
    upload_result = subprocess.run(upload_cmd.split(" "))
    assert upload_result == 0

    for job in ["cap", "smb", "crp"]:
        job_result = subprocess.run(["run_job.sh", environment, job])
        assert job_result.returncode == 0


def smoke_test_data():
    data = open("smoke_test_data.dat").read()
    data = data.replace("20250101", datetime.now().strftime("%Y%m%d"))
    return data
