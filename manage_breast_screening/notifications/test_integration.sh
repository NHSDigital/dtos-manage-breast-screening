#!/bin/bash
docker compose --profile test-integration run --build cmapi_stub pytest -v tests/integration
test_exit_code=$?
docker compose --profile test-integration down cmapi_stub --volumes
exit $test_exit_code