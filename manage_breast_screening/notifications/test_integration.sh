#!/bin/bash
docker compose --profile test-integration run --build integration-tests poetry run pytest -v manage_breast_screening/notifications/tests/integration/
test_exit_code=$?
docker compose --profile test-integration down cmapi_stub --volumes
exit $test_exit_code